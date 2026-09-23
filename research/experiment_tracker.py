#!/usr/bin/env python3
"""
Structured experiment tracking for reproducible research.

Lightweight alternative to MLflow that logs experiments to JSON/CSV
for traceability and comparison.

Usage:
    from experiment_tracker import ExperimentTracker
    
    tracker = ExperimentTracker("flagship_365d")
    tracker.log_params({"n_consumers": 200, "duration_days": 365})
    tracker.log_metrics({"ari": 0.813, "silhouette": 0.3283})
    tracker.save()
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import hashlib

class ExperimentTracker:
    """Track experiments with structured logging"""
    
    def __init__(self, experiment_name, output_dir="research/experiments"):
        self.experiment_name = experiment_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.data = {
            "experiment_name": experiment_name,
            "run_id": self.run_id,
            "timestamp": datetime.now().isoformat(),
            "params": {},
            "metrics": {},
            "artifacts": {},
            "metadata": {}
        }
    
    def log_param(self, key, value):
        """Log a single parameter"""
        self.data["params"][key] = value
    
    def log_params(self, params_dict):
        """Log multiple parameters"""
        self.data["params"].update(params_dict)
    
    def log_metric(self, key, value):
        """Log a single metric"""
        self.data["metrics"][key] = value
    
    def log_metrics(self, metrics_dict):
        """Log multiple metrics"""
        self.data["metrics"].update(metrics_dict)
    
    def log_artifact(self, name, path):
        """Log path to an artifact"""
        self.data["artifacts"][name] = str(path)
    
    def log_metadata(self, key, value):
        """Log metadata (versions, hashes, etc.)"""
        self.data["metadata"][key] = value
    
    def compute_config_hash(self):
        """Compute hash of params for reproducibility"""
        param_str = json.dumps(self.data["params"], sort_keys=True)
        return hashlib.sha256(param_str.encode()).hexdigest()[:16]
    
    def save(self):
        """Save experiment run to JSON"""
        # Add config hash
        self.data["metadata"]["config_hash"] = self.compute_config_hash()
        
        # Save individual run
        run_file = self.output_dir / f"{self.experiment_name}_{self.run_id}.json"
        with open(run_file, "w") as f:
            json.dump(self.data, f, indent=2)
        
        # Append to experiment log
        log_file = self.output_dir / f"{self.experiment_name}_log.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(self.data) + "\n")
        
        print(f"✓ Experiment logged: {run_file}")
        return run_file
    
    @staticmethod
    def load_experiments(experiment_name, output_dir="research/experiments"):
        """Load all runs for an experiment"""
        log_file = Path(output_dir) / f"{experiment_name}_log.jsonl"
        if not log_file.exists():
            return []
        
        experiments = []
        with open(log_file) as f:
            for line in f:
                experiments.append(json.loads(line))
        return experiments
    
    @staticmethod
    def experiments_to_dataframe(experiments):
        """Convert experiment list to pandas DataFrame"""
        if not experiments:
            return pd.DataFrame()
        
        rows = []
        for exp in experiments:
            row = {
                "run_id": exp["run_id"],
                "timestamp": exp["timestamp"],
                **exp["params"],
                **exp["metrics"],
                "config_hash": exp["metadata"].get("config_hash", "")
            }
            rows.append(row)
        
        return pd.DataFrame(rows)


def example_usage():
    """Example: Track flagship experiment"""
    tracker = ExperimentTracker("flagship_365d")
    
    # Log configuration
    tracker.log_params({
        "n_consumers": 200,
        "duration_days": 365,
        "random_seed": 42,
        "n_features": 51,
        "pca_threshold": 0.95
    })
    
    # Log results
    tracker.log_metrics({
        "selected_k": 4,
        "n_pca_components": 10,
        "ari": 0.813,
        "nmi": 0.828,
        "silhouette": 0.3283,
        "calinski_harabasz": 96.6,
        "davies_bouldin": 1.1691,
        "stability_ari": 0.9947,
        "temporal_ari_mean": 0.882
    })
    
    # Log artifacts
    tracker.log_artifacts({
        "metrics_csv": "outputs/metrics/clustering_metrics.csv",
        "model": "models/kmeans_model.pkl",
        "report": "outputs/reports/analysis_summary.md"
    })
    
    # Log metadata
    tracker.log_metadata("python_version", "3.11")
    tracker.log_metadata("scikit_learn_version", "1.9.0")
    
    # Save
    tracker.save()


if __name__ == "__main__":
    example_usage()
    
    # Load and display
    experiments = ExperimentTracker.load_experiments("flagship_365d")
    df = ExperimentTracker.experiments_to_dataframe(experiments)
    print("\nLoaded Experiments:")
    print(df.to_string())
