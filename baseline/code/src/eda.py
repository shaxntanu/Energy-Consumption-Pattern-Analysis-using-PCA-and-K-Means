"""
EDA Module
Performs exploratory data analysis and generates visualizations.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10


def plot_distributions(df: pd.DataFrame, columns: list, output_dir: str = 'outputs/figures'):
    """
    Plot distributions of specified columns.
    
    Args:
        df: Input DataFrame
        columns: List of columns to plot
        output_dir: Directory to save plots
    """
    logger.info(f"Plotting distributions for {len(columns)} columns")
    
    n_cols = min(3, len(columns))
    n_rows = (len(columns) + n_cols - 1) // n_cols
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 5 * n_rows))
    axes = axes.flatten() if n_rows > 1 else [axes]
    
    for i, col in enumerate(columns):
        if col in df.columns:
            axes[i].hist(df[col].dropna(), bins=30, edgecolor='black', alpha=0.7)
            axes[i].set_title(f'Distribution of {col}')
            axes[i].set_xlabel(col)
            axes[i].set_ylabel('Frequency')
        else:
            axes[i].text(0.5, 0.5, f'Column {col} not found', 
                        ha='center', va='center')
    
    # Hide unused subplots
    for i in range(len(columns), len(axes)):
        axes[i].set_visible(False)
    
    plt.tight_layout()
    output_path = Path(output_dir) / 'distributions.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved distributions plot to {output_path}")


def plot_hourly_patterns(df: pd.DataFrame, output_dir: str = 'outputs/figures'):
    """
    Plot hourly consumption patterns.
    
    Args:
        df: Input DataFrame with hour column
        output_dir: Directory to save plots
    """
    logger.info("Plotting hourly patterns")
    
    if 'hour' not in df.columns:
        logger.warning("Hour column not found")
        return
    
    hourly_avg = df.groupby('hour')['energy_consumption_kwh'].mean()
    
    plt.figure(figsize=(12, 6))
    plt.plot(hourly_avg.index, hourly_avg.values, marker='o', linewidth=2, markersize=8)
    plt.xlabel('Hour of Day')
    plt.ylabel('Average Energy Consumption (kWh)')
    plt.title('Average Hourly Energy Consumption Pattern')
    plt.grid(True, alpha=0.3)
    plt.xticks(range(24))
    
    output_path = Path(output_dir) / 'hourly_patterns.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved hourly patterns plot to {output_path}")


def plot_weekday_weekend_comparison(df: pd.DataFrame, output_dir: str = 'outputs/figures'):
    """
    Plot weekday vs weekend consumption comparison.
    
    Args:
        df: Input DataFrame with is_weekend column
        output_dir: Directory to save plots
    """
    logger.info("Plotting weekday vs weekend comparison")
    
    if 'is_weekend' not in df.columns:
        logger.warning("is_weekend column not found")
        return
    
    weekend_comparison = df.groupby('is_weekend')['energy_consumption_kwh'].mean()
    
    plt.figure(figsize=(8, 6))
    labels = ['Weekday', 'Weekend']
    colors = ['#3498db', '#e74c3c']
    plt.bar(labels, weekend_comparison.values, color=colors, alpha=0.7, edgecolor='black')
    plt.ylabel('Average Energy Consumption (kWh)')
    plt.title('Weekday vs Weekend Energy Consumption')
    plt.grid(True, alpha=0.3, axis='y')
    
    output_path = Path(output_dir) / 'weekday_weekend_comparison.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved weekday vs weekend plot to {output_path}")


def plot_correlation_heatmap(df: pd.DataFrame, output_dir: str = 'outputs/figures'):
    """
    Plot correlation heatmap of numerical features.
    
    Args:
        df: Input DataFrame
        output_dir: Directory to save plots
    """
    logger.info("Plotting correlation heatmap")
    
    # Select only numerical columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    correlation_matrix = df[numeric_cols].corr()
    
    plt.figure(figsize=(12, 10))
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0,
                square=True, linewidths=1, cbar_kws={"shrink": 0.8})
    plt.title('Correlation Heatmap of Energy Consumption Features')
    plt.tight_layout()
    
    output_path = Path(output_dir) / 'correlation_heatmap.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved correlation heatmap to {output_path}")


def plot_consumption_variability(df: pd.DataFrame, output_dir: str = 'outputs/figures'):
    """
    Plot consumption variability by consumer.
    
    Args:
        df: Input DataFrame with consumer_id
        output_dir: Directory to save plots
    """
    logger.info("Plotting consumption variability")
    
    if 'consumer_id' not in df.columns:
        logger.warning("consumer_id column not found")
        return
    
    consumer_stats = df.groupby('consumer_id')['energy_consumption_kwh'].agg(['mean', 'std'])
    consumer_stats['cv'] = consumer_stats['std'] / consumer_stats['mean']
    
    plt.figure(figsize=(12, 6))
    plt.scatter(consumer_stats['mean'], consumer_stats['cv'], alpha=0.6, s=50)
    plt.xlabel('Average Consumption (kWh)')
    plt.ylabel('Coefficient of Variation')
    plt.title('Consumption Variability by Consumer')
    plt.grid(True, alpha=0.3)
    
    output_path = Path(output_dir) / 'consumption_variability.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved consumption variability plot to {output_path}")


def plot_boxplots_by_time(df: pd.DataFrame, output_dir: str = 'outputs/figures'):
    """
    Plot boxplots of consumption by time periods.
    
    Args:
        df: Input DataFrame with temporal features
        output_dir: Directory to save plots
    """
    logger.info("Plotting boxplots by time periods")
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # By hour
    if 'hour' in df.columns:
        df.boxplot(column='energy_consumption_kwh', by='hour', ax=axes[0, 0])
        axes[0, 0].set_title('Consumption by Hour')
        axes[0, 0].set_xlabel('Hour')
        axes[0, 0].set_ylabel('Energy Consumption (kWh)')
    
    # By day of week
    if 'day_of_week' in df.columns:
        df.boxplot(column='energy_consumption_kwh', by='day_of_week', ax=axes[0, 1])
        axes[0, 1].set_title('Consumption by Day of Week')
        axes[0, 1].set_xlabel('Day of Week (0=Monday)')
        axes[0, 1].set_ylabel('Energy Consumption (kWh)')
    
    # By weekend
    if 'is_weekend' in df.columns:
        df.boxplot(column='energy_consumption_kwh', by='is_weekend', ax=axes[1, 0])
        axes[1, 0].set_title('Consumption by Weekend')
        axes[1, 0].set_xlabel('Is Weekend')
        axes[1, 0].set_ylabel('Energy Consumption (kWh)')
    
    # Overall distribution
    axes[1, 1].hist(df['energy_consumption_kwh'], bins=30, edgecolor='black', alpha=0.7)
    axes[1, 1].set_title('Overall Consumption Distribution')
    axes[1, 1].set_xlabel('Energy Consumption (kWh)')
    axes[1, 1].set_ylabel('Frequency')
    
    plt.tight_layout()
    output_path = Path(output_dir) / 'boxplots_by_time.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved boxplots to {output_path}")


def generate_statistical_summary(df: pd.DataFrame, output_dir: str = 'outputs/reports'):
    """
    Generate statistical summary report.
    
    Args:
        df: Input DataFrame
        output_dir: Directory to save report
    """
    logger.info("Generating statistical summary")
    
    # Numerical statistics
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    stats_summary = df[numeric_cols].describe()
    
    # Additional statistics
    skewness = df[numeric_cols].skew()
    kurtosis = df[numeric_cols].kurtosis()
    
    # Combine
    summary_df = pd.DataFrame({
        'Mean': stats_summary.loc['mean'],
        'Std': stats_summary.loc['std'],
        'Min': stats_summary.loc['min'],
        '25%': stats_summary.loc['25%'],
        '50%': stats_summary.loc['50%'],
        '75%': stats_summary.loc['75%'],
        'Max': stats_summary.loc['max'],
        'Skewness': skewness,
        'Kurtosis': kurtosis
    })
    
    output_path = Path(output_dir) / 'statistical_summary.csv'
    summary_df.to_csv(output_path)
    logger.info(f"Saved statistical summary to {output_path}")
    
    return summary_df


def run_eda_pipeline(df: pd.DataFrame, output_dir: str = 'outputs/figures'):
    """
    Run complete EDA pipeline.
    
    Args:
        df: Input DataFrame
        output_dir: Directory to save outputs
    """
    logger.info("Starting EDA pipeline")
    
    # Create output directories
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    Path('outputs/reports').mkdir(parents=True, exist_ok=True)
    
    # Generate plots
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    plot_distributions(df, numeric_cols[:6], output_dir)  # Limit to 6 columns
    plot_hourly_patterns(df, output_dir)
    plot_weekday_weekend_comparison(df, output_dir)
    plot_correlation_heatmap(df, output_dir)
    plot_consumption_variability(df, output_dir)
    plot_boxplots_by_time(df, output_dir)
    
    # Generate statistical summary
    summary = generate_statistical_summary(df)
    
    logger.info("EDA pipeline completed")
    return summary


if __name__ == "__main__":
    # Test EDA
    from data_loader import generate_synthetic_data
    from preprocessing import preprocess_pipeline
    from feature_engineering import engineer_all_features
    
    synthetic_data = generate_synthetic_data(n_consumers=100, n_days=7, hourly_records=True)
    preprocessed = preprocess_pipeline(synthetic_data)
    features = engineer_all_features(preprocessed)
    
    summary = run_eda_pipeline(preprocessed)
    print("\nStatistical Summary:")
    print(summary)
