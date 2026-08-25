"""
Dark Theme Configuration for Presentation Plots

Provides a centralized, premium dark theme for all presentation visualizations.
All plots use this consistent visual system for professional research presentations.
"""

import matplotlib.pyplot as plt
import matplotlib as mpl
from typing import Dict, List, Tuple
import numpy as np

# Color Palette - Premium Research Dashboard
COLORS = {
    # Background & Canvas
    'background': '#0B0F14',
    'canvas': '#0B0F14',
    
    # Text
    'text_primary': '#FFFFFF',  # Pure white
    'text_secondary': '#E0E0E0',  # Light gray
    'text_muted': '#A0A0A0',
    
    # Grid & Borders
    'grid': '#374151',
    'border': '#06B6D4',  # Bright cyan
    'edge': '#06B6D4',
    
    # Accent Colors - Bright Neon Palette
    'cyan': '#00D9FF',      # Bright cyan
    'teal': '#1DE9B6',      # Bright teal
    'emerald': '#00FF88',   # Bright emerald
    'green': '#76FF03',     # Neon green
    'lime': '#C6FF00',      # Bright lime
    'amber': '#FFD600',     # Bright amber
    'orange': '#FF9100',    # Bright orange
    'red': '#FF1744',       # Bright red
    'rose': '#FF4081',      # Bright rose
    'violet': '#B388FF',    # Bright violet
    'purple': '#E040FB',    # Bright purple
    'blue': '#448AFF',      # Bright blue
    'sky': '#00E5FF',       # Bright sky
}

# Cluster Colors - Consistent across all plots
CLUSTER_COLORS = [
    COLORS['cyan'],      # Cluster 0
    COLORS['violet'],    # Cluster 1
    COLORS['emerald'],   # Cluster 2
    COLORS['amber'],     # Cluster 3
    COLORS['sky'],       # Cluster 4
    COLORS['rose'],      # Cluster 5
    COLORS['lime'],      # Cluster 6
    COLORS['purple'],    # Cluster 7
]

# Feature Set Colors - For Ablation Studies
FEATURE_SET_COLORS = {
    'scale': COLORS['orange'],
    'shape': COLORS['cyan'],
    'summary': COLORS['violet'],
    'behavioral': COLORS['emerald'],
    'combined': COLORS['amber'],
}

# Sequential Colormap - For heatmaps (correlation, etc)
SEQUENTIAL_CMAP = 'viridis'

# Diverging Colormap - For difference plots, crosstabs
DIVERGING_CMAP = 'RdBu_r'


def apply_dark_theme() -> None:
    """
    Apply the centralized dark theme to matplotlib.
    Call this at the start of any plotting function.
    """
    # Don't use plt.style.use - set params directly
    mpl.rcParams.update({
        # Figure
        'figure.facecolor': COLORS['background'],
        'figure.edgecolor': COLORS['background'],
        'figure.figsize': (13.333, 7.5),  # 16:9 aspect ratio
        'figure.dpi': 100,
        'savefig.dpi': 300,
        'savefig.facecolor': COLORS['background'],
        'savefig.edgecolor': COLORS['background'],
        'savefig.bbox': 'tight',
        
        # Axes
        'axes.facecolor': COLORS['canvas'],
        'axes.edgecolor': COLORS['cyan'],  # Bright cyan border
        'axes.linewidth': 1.5,
        'axes.labelcolor': COLORS['text_primary'],
        'axes.labelsize': 12,
        'axes.titlesize': 14,
        'axes.titleweight': 'bold',
        'axes.titlecolor': COLORS['text_primary'],
        'axes.grid': True,
        'axes.axisbelow': True,
        'axes.spines.top': False,
        'axes.spines.right': False,
        
        # Grid
        'grid.color': COLORS['grid'],
        'grid.alpha': 0.4,
        'grid.linewidth': 0.8,
        'grid.linestyle': '-',
        
        # Ticks
        'xtick.color': COLORS['cyan'],  # Bright cyan ticks
        'xtick.labelsize': 10,
        'ytick.color': COLORS['cyan'],  # Bright cyan ticks
        'ytick.labelsize': 10,
        
        # Legend
        'legend.facecolor': COLORS['background'],
        'legend.edgecolor': COLORS['cyan'],
        'legend.framealpha': 0.9,
        'legend.fontsize': 10,
        
        # Lines - DEFAULT to bright cyan
        'lines.linewidth': 2.5,
        'lines.markersize': 8,
        'lines.color': COLORS['cyan'],
        
        # Patches (bars, etc) - DEFAULT to bright colors
        'patch.edgecolor': COLORS['cyan'],
        'patch.facecolor': COLORS['cyan'],
        'patch.linewidth': 1.0,
        
        # Boxplot colors
        'boxplot.boxprops.color': COLORS['cyan'],
        'boxplot.whiskerprops.color': COLORS['emerald'],
        'boxplot.capprops.color': COLORS['emerald'],
        'boxplot.medianprops.color': COLORS['amber'],
        'boxplot.flierprops.color': COLORS['rose'],
        'boxplot.flierprops.markeredgecolor': COLORS['rose'],
        
        # Scatter
        'scatter.edgecolors': COLORS['cyan'],
        
        # Text
        'text.color': COLORS['text_primary'],
        'font.size': 11,
        'font.family': 'sans-serif',
    })


def get_cluster_color(cluster_id: int) -> str:
    """Get consistent color for a cluster ID."""
    return CLUSTER_COLORS[cluster_id % len(CLUSTER_COLORS)]


def get_cluster_colors(n_clusters: int) -> List[str]:
    """Get list of colors for n clusters."""
    return [get_cluster_color(i) for i in range(n_clusters)]


def get_feature_set_color(feature_set: str) -> str:
    """Get color for a feature set in ablation studies."""
    return FEATURE_SET_COLORS.get(feature_set.lower(), COLORS['text_secondary'])


def get_sequential_colors(n: int, cmap: str = None) -> List[str]:
    """Get n colors from a sequential colormap."""
    if cmap is None:
        cmap = SEQUENTIAL_CMAP
    cm = plt.get_cmap(cmap)
    return [mpl.colors.rgb2hex(cm(i / (n - 1))) for i in range(n)]


def enhance_heatmap_readability(ax: plt.Axes, cmap: str = None) -> None:
    """
    Enhance heatmap readability on dark background.
    
    Args:
        ax: Matplotlib axes object with heatmap
        cmap: Colormap name (uses default if None)
    """
    # Ensure text is visible
    for text in ax.texts:
        text.set_color(COLORS['text_primary'])
        text.set_fontsize(9)
    
    # Style colorbar if present
    if hasattr(ax, 'collections') and len(ax.collections) > 0:
        cbar = ax.collections[0].colorbar
        if cbar:
            cbar.ax.yaxis.set_tick_params(color=COLORS['text_secondary'])
            cbar.outline.set_edgecolor(COLORS['border'])
            plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), 
                    color=COLORS['text_secondary'])


def style_correlation_heatmap(fig: plt.Figure, ax: plt.Axes) -> None:
    """
    Apply dark-mode styling specifically for correlation heatmaps.
    
    Args:
        fig: Matplotlib figure
        ax: Matplotlib axes
    """
    # Set background
    fig.patch.set_facecolor(COLORS['background'])
    ax.set_facecolor(COLORS['canvas'])
    
    # Style tick labels
    ax.tick_params(colors=COLORS['text_secondary'], labelsize=9)
    
    # Rotate labels for readability
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    plt.setp(ax.get_yticklabels(), rotation=0)


def add_presentation_title(ax: plt.Axes, title: str, subtitle: str = None) -> None:
    """
    Add a styled title optimized for presentation.
    
    Args:
        ax: Matplotlib axes
        title: Main title
        subtitle: Optional subtitle
    """
    if subtitle:
        full_title = f"{title}\n{subtitle}"
    else:
        full_title = title
    
    ax.set_title(full_title, fontsize=14, fontweight='normal', 
                color=COLORS['text_primary'], pad=15)


def configure_legend(ax: plt.Axes, **kwargs) -> None:
    """
    Configure legend with dark theme styling.
    
    Args:
        ax: Matplotlib axes
        **kwargs: Additional legend arguments
    """
    legend_params = {
        'facecolor': COLORS['background'],
        'edgecolor': COLORS['border'],
        'framealpha': 0.9,
        'fontsize': 10,
        'loc': 'best',
    }
    legend_params.update(kwargs)
    
    legend = ax.legend(**legend_params)
    if legend:
        plt.setp(legend.get_texts(), color=COLORS['text_primary'])


def get_archetype_colors() -> List[str]:
    """Get consistent colors for the 4 archetypes."""
    return [
        COLORS['cyan'],      # Archetype 0
        COLORS['emerald'],   # Archetype 1
        COLORS['violet'],    # Archetype 2
        COLORS['amber'],     # Archetype 3
    ]


def get_metric_color(metric_name: str) -> str:
    """
    Get appropriate color for different metrics.
    
    Args:
        metric_name: Name of the metric
        
    Returns:
        Hex color string
    """
    metric_map = {
        'silhouette': COLORS['cyan'],
        'davies': COLORS['violet'],
        'calinski': COLORS['emerald'],
        'inertia': COLORS['amber'],
        'ari': COLORS['sky'],
        'nmi': COLORS['teal'],
    }
    
    for key, color in metric_map.items():
        if key in metric_name.lower():
            return color
    
    return COLORS['text_secondary']
