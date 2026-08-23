"""
Recommendation Engine Module

Turns measured cluster characteristics into suggestions to investigate. Every
suggestion is a row with five fields, in this order:

- observation: what was measured about the cluster
- evidence: the comparison that triggered the row
- cluster_value: the cluster's value for that metric
- population_value: the same metric across all consumers
- action: what to consider doing about it

Three rules constrain what this module is allowed to say:

1. Triggers are relative to the population, never absolute thresholds. An
   absolute cutoff such as "mean above 2.0 kWh" is meaningless on a synthetic
   dataset whose units are arbitrary, and would fire or not fire depending on how
   the generator was parameterized.
2. No savings figures. The analysis measures when energy is used; it contains no
   information about what would happen if that changed.
3. No causal language. Cluster membership is an observed association. A row says
   what is worth testing, not what will work.

The data behind these rows is synthetic, so nothing here is a finding about real
households. It is a demonstration that the pipeline produces actionable output
when given real data.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Relative gap from the population needed before a row is emitted.
HIGH_TRIGGER = 1.15
LOW_TRIGGER = 0.85

# Absolute relative deviation that separates the priority bands.
PRIORITY_HIGH = 0.30
PRIORITY_MEDIUM = 0.15

CATEGORY_ORDER = {
    'timing': 0,
    'peak_management': 1,
    'weekend': 2,
    'variability': 3,
    'scale': 4,
}

PRIORITY_ORDER = {'high': 0, 'medium': 1, 'low': 2}


@dataclass(frozen=True)
class Rule:
    """One trigger and the text it produces.

    Attributes:
        metric: Profile column the rule reads.
        direction: 'high' fires when the cluster exceeds the population by
            HIGH_TRIGGER, 'low' fires when it falls below by LOW_TRIGGER.
        category: Grouping used for ordering and reporting.
        observation: What was measured, as a sentence.
        action: What to consider, as a sentence.
        unit: Formatting hint. 'share' prints percentages, '' prints raw values.
    """

    metric: str
    direction: str
    category: str
    observation: str
    action: str
    unit: str = ''


RULES: List[Rule] = [
    Rule(
        metric='evening_share',
        direction='high',
        category='timing',
        observation='A larger share of this cluster\'s daily energy falls in the evening block (18:00 to 24:00) than for the population.',
        action='Check which evening loads are deferrable, such as water heating, laundry and dishwashing, and test whether a time-of-use signal moves them. Measure the effect on a subset before assuming any change.',
        unit='share',
    ),
    Rule(
        metric='afternoon_share',
        direction='high',
        category='timing',
        observation='This cluster concentrates its energy in the midday block (12:00 to 18:00).',
        action='Midday demand overlaps the hours when rooftop solar generates most, so evaluate on-site generation or a midday tariff for this group before considering load shifting.',
        unit='share',
    ),
    Rule(
        metric='morning_share',
        direction='high',
        category='timing',
        observation='This cluster concentrates its energy in the morning block (06:00 to 12:00).',
        action='Look for a fixed morning routine driving the peak. Loads tied to a departure time are harder to shift than discretionary ones, so confirm which is which before proposing a schedule change.',
        unit='share',
    ),
    Rule(
        metric='night_share',
        direction='high',
        category='timing',
        observation='This cluster draws an unusually large share of its energy overnight (00:00 to 06:00), when household activity is normally low.',
        action='Investigate standing load rather than behaviour. A high overnight share usually points at equipment that runs continuously, which responds to efficiency measures and not to scheduling.',
        unit='share',
    ),
    Rule(
        metric='peak_to_avg_ratio',
        direction='high',
        category='peak_management',
        observation='This cluster reaches a higher peak relative to its own average than the population does.',
        action='This group contributes disproportionately to peak demand, so it is where demand limiting or a capacity-based tariff would have the most effect. Confirm the peaks are coincident with system peak before acting.',
    ),
    Rule(
        metric='peak_to_avg_ratio',
        direction='low',
        category='peak_management',
        observation='This cluster stays close to its own average all day, with a lower peak-to-average ratio than the population.',
        action='There is little peak to manage here. Any reduction has to come from the level of the base load, not from moving it in time.',
    ),
    Rule(
        metric='weekend_ratio',
        direction='high',
        category='weekend',
        observation='This cluster uses more energy on weekend days relative to weekdays than the population does.',
        action='Weekend exposure matters for this group, so check whether the tariff in force distinguishes weekends. A weekday-only time-of-use schedule would miss most of their consumption.',
    ),
    Rule(
        metric='weekend_ratio',
        direction='low',
        category='weekend',
        observation='This cluster uses less energy on weekend days relative to weekdays than the population does.',
        action='Consumption is concentrated on weekdays, which is consistent with an occupancy pattern tied to a working week. Weekday-targeted measures reach this group; weekend measures largely do not.',
    ),
    Rule(
        metric='weekend_shape_distance',
        direction='high',
        category='weekend',
        observation='This cluster\'s weekend timing differs more from its weekday timing than is typical.',
        action='A single fixed daily schedule fits this group poorly. If a time-of-use scheme is applied, evaluate weekday and weekend windows separately.',
    ),
    Rule(
        metric='coefficient_of_variation',
        direction='high',
        category='variability',
        observation='Consumption within this cluster varies more from hour to hour than the population average.',
        action='Short-term forecasts for this group will carry more error, so allow for that when sizing reserve or planning storage. Sub-metering would show whether the variation comes from one device or from many.',
    ),
    Rule(
        metric='coefficient_of_variation',
        direction='low',
        category='variability',
        observation='Consumption within this cluster is steadier from hour to hour than the population average.',
        action='Predictable demand makes this group a reasonable baseline for forecasting and for measuring the effect of any intervention on the other clusters.',
    ),
    Rule(
        metric='mean_kwh',
        direction='high',
        category='scale',
        observation='For context only, and not part of the behavioral clustering: mean consumption per record is above the population mean.',
        action='In absolute terms a given percentage reduction is worth more here than in a lower-consuming cluster. Note that this cluster was formed on usage timing, not on magnitude, so its members do not all consume a lot.',
        unit='kwh',
    ),
]


def _format_value(value: float, unit: str) -> str:
    """Render a metric value according to its unit hint."""
    if unit == 'share':
        return f"{value:.1%}"
    if unit == 'kwh':
        return f"{value:.3f} kWh"
    return f"{value:.3f}"


def _priority_for(relative: float) -> str:
    """Band a relative deviation into high, medium or low priority.

    Priority reflects how far the cluster sits from the population, nothing else.
    It is not a claim about how much energy or money is involved.

    Args:
        relative: Cluster value divided by population value.

    Returns:
        'high', 'medium' or 'low'.
    """
    deviation = abs(relative - 1.0)
    if deviation >= PRIORITY_HIGH:
        return 'high'
    if deviation >= PRIORITY_MEDIUM:
        return 'medium'
    return 'low'


def evaluate_rules(profile: dict,
                   baseline: Dict[str, float],
                   rules: Optional[List[Rule]] = None) -> List[dict]:
    """Apply every rule to one cluster profile.

    Args:
        profile: One row of the profiles frame as a dictionary.
        baseline: Population baseline from cluster_profiling.population_baseline.
        rules: Rules to evaluate. Defaults to RULES.

    Returns:
        List of recommendation dictionaries, unordered.
    """
    rules = rules if rules is not None else RULES
    rows = []

    for rule in rules:
        cluster_value = profile.get(rule.metric)
        population_value = baseline.get(rule.metric)

        if cluster_value is None or population_value is None:
            continue
        if not np.isfinite(cluster_value) or not np.isfinite(population_value):
            continue
        if population_value == 0:
            continue

        relative = float(cluster_value) / float(population_value)
        fires = relative >= HIGH_TRIGGER if rule.direction == 'high' else relative <= LOW_TRIGGER
        if not fires:
            continue

        comparison = 'above' if relative > 1 else 'below'
        rows.append({
            'metric': rule.metric,
            'category': rule.category,
            'observation': rule.observation,
            'evidence': (
                f"{rule.metric} is {_format_value(float(cluster_value), rule.unit)} "
                f"against a population {_format_value(float(population_value), rule.unit)}, "
                f"{abs(relative - 1):.0%} {comparison} the population value."
            ),
            'cluster_value': float(cluster_value),
            'population_value': float(population_value),
            'relative_to_population': relative,
            'action': rule.action,
            'priority': _priority_for(relative),
        })

    return rows


def prioritize_recommendations(recommendations: List[dict]) -> List[dict]:
    """Order rows by priority, then category, then size of the deviation.

    The ordering is total and deterministic, so the same profiles always produce
    the same report.

    Args:
        recommendations: Rows from evaluate_rules.

    Returns:
        Ordered list.
    """
    return sorted(
        recommendations,
        key=lambda row: (
            PRIORITY_ORDER.get(row['priority'], 2),
            CATEGORY_ORDER.get(row['category'], len(CATEGORY_ORDER)),
            -abs(row['relative_to_population'] - 1.0),
            row['metric'],
        ),
    )


def generate_cluster_recommendations(profiles: pd.DataFrame,
                                     baseline: Dict[str, float]) -> pd.DataFrame:
    """Build the recommendation table for every cluster.

    Args:
        profiles: Named profiles frame from cluster_profiling.
        baseline: Population baseline.

    Returns:
        DataFrame with one row per triggered rule per cluster.
    """
    logger.info("Generating recommendations from measured cluster deviations")

    rows = []
    for _, profile in profiles.iterrows():
        profile_dict = profile.to_dict()
        cluster_id = int(profile_dict['cluster'])
        cluster_name = profile_dict.get('cluster_name', f'Cluster {cluster_id}')

        triggered = prioritize_recommendations(evaluate_rules(profile_dict, baseline))
        if not triggered:
            logger.info(f"Cluster {cluster_id} sits close to the population on every metric")

        for rank, row in enumerate(triggered, start=1):
            rows.append({
                'cluster': cluster_id,
                'cluster_name': cluster_name,
                'rank': rank,
                'priority': row['priority'],
                'category': row['category'],
                'observation': row['observation'],
                'evidence': row['evidence'],
                'cluster_value': row['cluster_value'],
                'population_value': row['population_value'],
                'relative_to_population': row['relative_to_population'],
                'action': row['action'],
            })

    frame = pd.DataFrame(rows, columns=[
        'cluster', 'cluster_name', 'rank', 'priority', 'category', 'observation',
        'evidence', 'cluster_value', 'population_value', 'relative_to_population', 'action',
    ])

    logger.info(f"Generated {len(frame)} rows across {len(profiles)} clusters")
    return frame


def generate_recommendations_report(recommendations: pd.DataFrame, output_dir: str) -> None:
    """Write the recommendation table as a readable markdown report."""
    logger.info("Writing recommendations report")

    lines = [
        "# Recommendations",
        "",
        "## What this file is",
        "",
        "Each row below was produced by comparing one measured cluster metric with the",
        "same metric across all consumers. A row appears only when the cluster sits at",
        "least 15 percent above or below the population value.",
        "",
        "Three things this file does not contain:",
        "",
        "- Savings figures. The analysis measures when energy is used. It contains no",
        "  information about what would happen if that changed.",
        "- Causal claims. Cluster membership is an observed association, so every action",
        "  below is something to test rather than something known to work.",
        "- Findings about real households. The underlying data is synthetic.",
        "",
        "Priority reflects only how far the cluster sits from the population: high is a",
        "deviation of 30 percent or more, medium 15 percent or more.",
        "",
    ]

    if recommendations.empty:
        lines += [
            "## Result",
            "",
            "No cluster deviated from the population by enough to trigger a rule. That is",
            "a real outcome and is reported as such rather than filled with generic advice.",
            "",
        ]
    else:
        for cluster_id in sorted(recommendations['cluster'].unique()):
            rows = recommendations[recommendations['cluster'] == cluster_id].sort_values('rank')
            lines += [f"## Cluster {cluster_id}: {rows.iloc[0]['cluster_name']}", ""]
            for _, row in rows.iterrows():
                lines += [
                    f"### {row['rank']}. {row['category'].replace('_', ' ').title()} "
                    f"({row['priority']} priority)",
                    "",
                    f"- Observation: {row['observation']}",
                    f"- Evidence: {row['evidence']}",
                    f"- Cluster value: {row['cluster_value']:.4f}",
                    f"- Population baseline: {row['population_value']:.4f}",
                    f"- Action: {row['action']}",
                    "",
                ]

    path = Path(output_dir) / 'recommendations_report.md'
    path.write_text("\n".join(lines), encoding='utf-8')
    logger.info(f"Recommendations report saved to {path}")


def save_recommendations(recommendations: pd.DataFrame,
                         output_dir: str = 'outputs/reports') -> None:
    """Write the recommendation table as CSV and as a markdown report."""
    logger.info("Saving recommendations")

    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    recommendations.to_csv(path / 'recommendations.csv', index=False)
    generate_recommendations_report(recommendations, str(path))

    logger.info(f"Recommendations saved to {path}")


def run_recommendation_engine(profiles: pd.DataFrame,
                              baseline: Dict[str, float],
                              output_dir: str = 'outputs/reports') -> pd.DataFrame:
    """Build and save the recommendation table.

    Args:
        profiles: Named profiles frame from cluster_profiling.
        baseline: Population baseline from cluster_profiling.
        output_dir: Directory for the CSV and markdown outputs.

    Returns:
        The recommendation table.
    """
    logger.info("Starting recommendation engine")

    recommendations = generate_cluster_recommendations(profiles, baseline)
    save_recommendations(recommendations, output_dir)

    logger.info("Recommendation engine completed")
    return recommendations


if __name__ == "__main__":
    from project_paths import anchor_to_project_root

    anchor_to_project_root()

    from cluster_profiling import run_cluster_profiling
    from clustering import run_clustering_pipeline
    from data_loader import generate_synthetic_data
    from feature_engineering import engineer_all_features, select_features
    from pca_analysis import run_pca_pipeline
    from preprocessing import preprocess_pipeline

    raw = generate_synthetic_data(n_consumers=200, n_days=30, hourly_records=True)
    preprocessed = preprocess_pipeline(raw.drop(columns=['archetype']))
    behavioral = select_features(
        engineer_all_features(preprocessed, feature_set='behavioral'),
        feature_group='behavioral',
    )

    X_pca, pca, scaler, n_components = run_pca_pipeline(behavioral)
    clustering = run_clustering_pipeline(X_pca, test_stability=False)

    combined = engineer_all_features(preprocessed, feature_set='combined')
    profiles, insights, baseline = run_cluster_profiling(combined, clustering.labels)

    recommendations = run_recommendation_engine(profiles, baseline)

    print(f"\n{len(recommendations)} rows generated")
    if not recommendations.empty:
        print(recommendations[['cluster', 'cluster_name', 'rank', 'priority',
                               'category', 'evidence']].to_string(index=False))
