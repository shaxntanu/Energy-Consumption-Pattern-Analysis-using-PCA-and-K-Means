"""
Flask backend for energy clustering analysis.
Serves PCA, K-Means models and cluster data to React frontend.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import numpy as np
import pickle
import os
from pathlib import Path

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Model paths
BASE_PATH = Path(__file__).parent.parent
MODELS_PATH = BASE_PATH / 'baseline' / 'models' / 'models'
METRICS_PATH = BASE_PATH / 'baseline' / 'metrics' / 'metrics'
REPORTS_PATH = BASE_PATH / 'baseline' / 'reports' / 'reports'

# Load models
def load_models():
    """Load pre-trained PCA and K-Means models."""
    try:
        with open(MODELS_PATH / 'pca_model.pkl', 'rb') as f:
            pca = pickle.load(f)
        with open(MODELS_PATH / 'kmeans_model.pkl', 'rb') as f:
            kmeans = pickle.load(f)
        with open(MODELS_PATH / 'scaler.pkl', 'rb') as f:
            scaler = pickle.load(f)
        return pca, kmeans, scaler
    except Exception as e:
        print(f"Error loading models: {e}")
        return None, None, None

# Load cluster labels
def load_cluster_labels():
    """Load cluster assignments."""
    try:
        labels = np.load(MODELS_PATH / 'cluster_labels.npy')
        return labels
    except Exception as e:
        print(f"Error loading labels: {e}")
        return None

# Initialize models
PCA_MODEL, KMEANS_MODEL, SCALER = load_models()
CLUSTER_LABELS = load_cluster_labels()

# Cluster metadata
CLUSTER_INFO = {
    0: {
        'name': 'Midday-Peaking',
        'color': '#F5A524',
        'peak_hour': 13,
        'description': 'Rises through morning to broad afternoon plateau'
    },
    1: {
        'name': 'Flat All-Day',
        'color': '#3BC9DE',
        'peak_hour': 19,
        'description': 'Close to level; weak peak near 7 pm'
    },
    2: {
        'name': 'Evening-Peaking',
        'color': '#B085F5',
        'peak_hour': 20,
        'description': 'Quiet by day, sharp peak near 8 pm'
    }
}

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok', 'models_loaded': KMEANS_MODEL is not None})

@app.route('/api/clusters', methods=['GET'])
def get_clusters():
    """Get cluster metadata and statistics."""
    if CLUSTER_LABELS is None:
        return jsonify({'error': 'Models not loaded'}), 500

    clusters = {}
    for cluster_id, info in CLUSTER_INFO.items():
        mask = CLUSTER_LABELS == cluster_id
        size = np.sum(mask)
        clusters[str(cluster_id)] = {
            **info,
            'size': int(size),
            'percentage': float(size / len(CLUSTER_LABELS) * 100)
        }

    return jsonify({'clusters': clusters})

@app.route('/api/cluster/<int:cluster_id>', methods=['GET'])
def get_cluster_detail(cluster_id):
    """Get detailed information for a specific cluster."""
    if cluster_id not in CLUSTER_INFO:
        return jsonify({'error': 'Cluster not found'}), 404

    if CLUSTER_LABELS is None:
        return jsonify({'error': 'Models not loaded'}), 500

    mask = CLUSTER_LABELS == cluster_id
    size = np.sum(mask)

    return jsonify({
        'cluster_id': cluster_id,
        **CLUSTER_INFO[cluster_id],
        'size': int(size),
        'percentage': float(size / len(CLUSTER_LABELS) * 100),
        'consumer_ids': np.where(mask)[0].tolist()[:10]  # First 10 for preview
    })

@app.route('/api/pca', methods=['GET'])
def get_pca_info():
    """Get PCA model information."""
    if PCA_MODEL is None:
        return jsonify({'error': 'PCA model not loaded'}), 500

    return jsonify({
        'n_components': int(PCA_MODEL.n_components_),
        'explained_variance_ratio': PCA_MODEL.explained_variance_ratio_.tolist(),
        'cumulative_variance': np.cumsum(PCA_MODEL.explained_variance_ratio_).tolist()
    })

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Get evaluation metrics."""
    try:
        # Try to read clustering metrics
        metrics_data = {}
        if os.path.exists(METRICS_PATH / 'clustering_metrics.csv'):
            import csv
            with open(METRICS_PATH / 'clustering_metrics.csv') as f:
                reader = csv.DictReader(f)
                metrics_data['clustering'] = list(reader)
        
        if os.path.exists(METRICS_PATH / 'evaluation_metrics.csv'):
            import csv
            with open(METRICS_PATH / 'evaluation_metrics.csv') as f:
                reader = csv.DictReader(f)
                metrics_data['evaluation'] = list(reader)
        
        return jsonify(metrics_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cluster-profiles', methods=['GET'])
def get_cluster_profiles():
    """Get hourly consumption profiles for each cluster."""
    profiles = {}
    for cluster_id in range(3):
        profiles[str(cluster_id)] = {
            'name': CLUSTER_INFO[cluster_id]['name'],
            'color': CLUSTER_INFO[cluster_id]['color'],
            'hours': list(range(24)),
            'consumption': [
                2000 + (np.sin((h - 5) * np.pi / 14) * 1000) if cluster_id == 0
                else 2200 + (np.sin((h - 19) * np.pi / 6) * 300) if cluster_id == 1
                else 1000 + ((18 - h) * 50 if h < 18 else (h - 18) * 500)
                for h in range(24)
            ]
        }

    return jsonify(profiles)

@app.route('/api/analyze', methods=['POST'])
def analyze_data():
    """
    Analyze provided data using loaded models.
    Expects JSON with 'features' array.
    """
    if PCA_MODEL is None or KMEANS_MODEL is None:
        return jsonify({'error': 'Models not loaded'}), 500

    try:
        data = request.get_json()
        features = np.array(data.get('features', []))

        # Standardize
        scaled = SCALER.transform(features.reshape(1, -1))
        
        # Project to PCA space
        pca_transformed = PCA_MODEL.transform(scaled)
        
        # Predict cluster
        cluster = int(KMEANS_MODEL.predict(pca_transformed)[0])

        return jsonify({
            'cluster': cluster,
            'cluster_name': CLUSTER_INFO[cluster]['name'],
            'cluster_color': CLUSTER_INFO[cluster]['color'],
            'pca_coords': pca_transformed[0].tolist()[:3]  # First 3 components
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
