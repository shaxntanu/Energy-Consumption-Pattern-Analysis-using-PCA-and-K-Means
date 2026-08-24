"""
Matplotlib plot rendering service.
Generates and serves cluster visualizations as PNG/SVG.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from io import BytesIO
import base64
from pathlib import Path

# Configuration
FIGURE_DPI = 100
FIGURE_SIZE = (12, 6)
DARK_BG = '#0B0E14'
PANEL_BG = '#141A24'
LINE_COLOR = '#262E3D'
INK_COLOR = '#EAECEF'
MIST_COLOR = '#8A93A6'
CYAN_COLOR = '#3BC9DE'

CLUSTER_COLORS = {
    0: '#F5A524',  # Midday-Peaking
    1: '#3BC9DE',  # Flat All-Day
    2: '#B085F5'   # Evening-Peaking
}

def generate_hourly_profile(cluster_id: int) -> np.ndarray:
    """Generate synthetic hourly profile for a cluster."""
    hours = np.arange(24)
    
    if cluster_id == 0:  # Midday-Peaking
        profile = 2000 + (np.sin((hours - 5) * np.pi / 14) * 1000)
    elif cluster_id == 1:  # Flat All-Day
        profile = 2200 + (np.sin((hours - 19) * np.pi / 6) * 300)
    else:  # Evening-Peaking
        profile = np.where(
            hours < 18,
            1000 + (18 - hours) * 50,
            1000 + (hours - 18) * 500
        )
    
    return np.maximum(500, profile)

def generate_cluster_profile_chart(cluster_id: int) -> str:
    """Generate hourly profile chart as base64 PNG."""
    profile = generate_hourly_profile(cluster_id)
    hours = np.arange(24)
    
    fig, ax = plt.subplots(figsize=FIGURE_SIZE, dpi=FIGURE_DPI)
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(PANEL_BG)
    
    # Plot
    color = CLUSTER_COLORS[cluster_id]
    ax.fill_between(hours, profile, alpha=0.3, color=color)
    ax.plot(hours, profile, color=color, linewidth=2.5, marker='o', markersize=6)
    
    # Styling
    ax.set_xlabel('Hour of Day', color=MIST_COLOR, fontsize=11)
    ax.set_ylabel('Consumption (kWh)', color=MIST_COLOR, fontsize=11)
    ax.set_xlim(-0.5, 23.5)
    ax.set_xticks(range(0, 24, 3))
    ax.grid(True, alpha=0.2, color=LINE_COLOR, linestyle='--')
    ax.tick_params(colors=MIST_COLOR)
    
    # Spine styling
    for spine in ax.spines.values():
        spine.set_color(LINE_COLOR)
    
    # Convert to base64
    buffer = BytesIO()
    plt.savefig(buffer, format='png', facecolor=DARK_BG, bbox_inches='tight')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode()
    plt.close(fig)
    
    return f"data:image/png;base64,{img_base64}"

def generate_comparison_chart() -> str:
    """Generate comparison chart of all three clusters."""
    fig, ax = plt.subplots(figsize=FIGURE_SIZE, dpi=FIGURE_DPI)
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(PANEL_BG)
    
    hours = np.arange(24)
    
    for cluster_id in range(3):
        profile = generate_hourly_profile(cluster_id)
        color = CLUSTER_COLORS[cluster_id]
        ax.plot(hours, profile, label=f'Cluster {cluster_id}', 
                color=color, linewidth=2.5, marker='o', markersize=5)
    
    # Styling
    ax.set_xlabel('Hour of Day', color=MIST_COLOR, fontsize=11)
    ax.set_ylabel('Consumption (kWh)', color=MIST_COLOR, fontsize=11)
    ax.set_xlim(-0.5, 23.5)
    ax.set_xticks(range(0, 24, 3))
    ax.grid(True, alpha=0.2, color=LINE_COLOR, linestyle='--')
    ax.tick_params(colors=MIST_COLOR)
    ax.legend(facecolor=PANEL_BG, edgecolor=LINE_COLOR, labelcolor=INK_COLOR)
    
    # Spine styling
    for spine in ax.spines.values():
        spine.set_color(LINE_COLOR)
    
    # Convert to base64
    buffer = BytesIO()
    plt.savefig(buffer, format='png', facecolor=DARK_BG, bbox_inches='tight')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode()
    plt.close(fig)
    
    return f"data:image/png;base64,{img_base64}"

def generate_distribution_chart() -> str:
    """Generate cluster size distribution chart."""
    fig, ax = plt.subplots(figsize=(8, 6), dpi=FIGURE_DPI)
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(PANEL_BG)
    
    clusters = ['Midday-Peaking', 'Flat All-Day', 'Evening-Peaking']
    sizes = [94, 57, 49]
    colors = list(CLUSTER_COLORS.values())
    
    bars = ax.bar(clusters, sizes, color=colors, alpha=0.8, edgecolor=LINE_COLOR, linewidth=1.5)
    
    # Add value labels
    for bar, size in zip(bars, sizes):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(size)}',
                ha='center', va='bottom', color=INK_COLOR, fontweight='bold')
    
    # Styling
    ax.set_ylabel('Number of Consumers', color=MIST_COLOR, fontsize=11)
    ax.tick_params(colors=MIST_COLOR)
    ax.grid(True, alpha=0.2, axis='y', color=LINE_COLOR, linestyle='--')
    
    # Spine styling
    for spine in ax.spines.values():
        spine.set_color(LINE_COLOR)
    
    plt.xticks(rotation=0, color=MIST_COLOR)
    
    # Convert to base64
    buffer = BytesIO()
    plt.savefig(buffer, format='png', facecolor=DARK_BG, bbox_inches='tight')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode()
    plt.close(fig)
    
    return f"data:image/png;base64,{img_base64}"

if __name__ == '__main__':
    # Test generation
    print("Generating plots...")
    for i in range(3):
        img = generate_cluster_profile_chart(i)
        print(f"Cluster {i} profile: {len(img)} bytes")
    
    comp = generate_comparison_chart()
    print(f"Comparison chart: {len(comp)} bytes")
    
    dist = generate_distribution_chart()
    print(f"Distribution chart: {len(dist)} bytes")
