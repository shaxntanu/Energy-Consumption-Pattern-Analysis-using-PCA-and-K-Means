# Energy Consumption Pattern Analysis

> **Discovering daily energy rhythms using machine learning**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Vercel-000000?style=for-the-badge&logo=vercel)](https://energy-consumption-pattern.vercel.app)
[![Interactive Simulator](https://img.shields.io/badge/Simulator-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit)](https://energy-consumption-pattern-vqrh.streamlit.app/)

## 🎯 What This Project Does

Ever wondered if there are patterns in how people use electricity throughout the day? This project finds those patterns automatically.

**In simple terms:**
- We analyze 200 households' hourly electricity usage over 30 days
- Machine learning groups them into 3 distinct patterns based on *when* they use energy, not *how much*
- The results show clear daily rhythms: some peak at midday, others in the evening, and some stay flat all day

**Why this matters:**
- Helps utilities understand customer behavior without invading privacy
- Can optimize energy grid operations and pricing
- Reveals insights for energy efficiency programs

## 🌐 Try It Live

**[📊 Interactive Web Dashboard](https://energy-consumption-pattern.vercel.app)** - Explore the analysis results with beautiful visualizations

**[🔬 Streamlit Simulator](https://energy-consumption-pattern-vqrh.streamlit.app/)** - Adjust parameters and see how the clustering changes

## 📊 Visual Results

### Daily Load Patterns by Cluster

Three distinct energy usage patterns emerged from the data:

![Hourly Load Patterns](baseline/figures/figures/hourly_patterns.png)

**What you're seeing:** Each line shows the average hourly electricity usage for one cluster. Notice how different groups peak at different times of day.

### Cluster Comparison

![Weekday vs Weekend](baseline/figures/figures/weekday_weekend_comparison.png)

**What you're seeing:** How energy patterns change between weekdays and weekends for each cluster.

### The Three Patterns We Found

| Pattern | Size | Peak Time | Description |
|---------|------|-----------|-------------|
| **Midday-Peaking** | 94 households (47%) | 1 PM | Usage rises through morning, plateaus in afternoon |
| **Flat All-Day** | 57 households (28%) | 7 PM | Steady throughout day with weak evening peak |
| **Evening-Peaking** | 49 households (25%) | 8 PM | Quiet by day, sharp spike after dark |

### How We Group Similar Patterns

![2D Cluster Visualization](baseline/figures/figures/cluster_visualization_2d.png)

**What you're seeing:** Each dot is a household. Colors show which group they belong to. Close dots have similar energy patterns.

### Choosing the Right Number of Groups

![Elbow Curve](baseline/figures/figures/elbow_curve.png)

**What you're seeing:** This chart helps us pick 3 groups as the sweet spot - not too many, not too few.

![Silhouette Scores](baseline/figures/figures/silhouette_scores.png)

**What you're seeing:** Higher scores mean better separation between groups. K=3 gives us clear, distinct patterns.

### Understanding the Data Better

![Distribution of Values](baseline/figures/figures/distributions.png)

**What you're seeing:** How different energy usage measurements are spread across all households.

![Correlation Heatmap](baseline/figures/figures/correlation_heatmap.png)

**What you're seeing:** Which energy measurements tend to move together (darker colors = stronger relationship).

### Dimensionality Reduction (PCA)

![Explained Variance](baseline/figures/figures/explained_variance.png)

**What you're seeing:** We compress 51 features down to 14 components while keeping 95% of the important information.

![PCA 2D Projection](baseline/figures/figures/pca_projection_2d.png)

**What you're seeing:** The entire dataset squeezed into 2 dimensions, showing natural groupings.

![Component Loadings](baseline/figures/figures/component_loadings.png)

**What you're seeing:** Which original features matter most for each compressed component.

### Variability Analysis

![Consumption Variability](baseline/figures/figures/consumption_variability.png)

**What you're seeing:** How much energy usage fluctuates throughout the day for each cluster.

![Boxplots by Time](baseline/figures/figures/boxplots_by_time.png)

**What you're seeing:** Statistical distribution of energy usage at different times of day.

## 🔬 How It Works

### The Simple Explanation

1. **Collect data** - Track electricity usage every hour for 200 homes over 30 days
2. **Extract features** - Calculate things like "what % of daily energy is used in the morning?"
3. **Reduce complexity** - Use PCA to simplify 51 measurements into 14 key numbers
4. **Find patterns** - K-Means clustering automatically groups similar households
5. **Analyze results** - See which patterns emerge and what they mean

### The Technical Details

**Data:**
- 200 synthetic consumers (generated with realistic patterns)
- 30 days of hourly readings
- 144,000 total data points

**Features Engineered:**
- 24 hourly consumption values
- 4 time-of-day shares (morning, afternoon, evening, night)
- Statistical measures (peak hour, base load, variation coefficient)

**Machine Learning Pipeline:**
1. **Standardization** - Scale all features to mean=0, std=1
2. **PCA** - Reduce 51 features → 14 components (95.3% variance retained)
3. **K-Means** - Cluster into K=3 groups (selected via Silhouette score)
4. **Validation** - Multiple metrics confirm good separation

**Evaluation Metrics:**
- Silhouette Score: 0.34 (modest but useful separation)
- Davies-Bouldin Index: Lower is better
- Calinski-Harabasz Score: Higher is better
- Gap Statistic: Confirms K=3 is optimal

## 🚀 Run It Yourself

### Quick Start

```bash
# Clone the repository
git clone https://github.com/shaxntanu/Energy-Consumption-Pattern-Analysis-using-PCA-and-K-Means.git
cd Energy-Consumption-Pattern-Analysis-using-PCA-and-K-Means

# Install dependencies
pip install -r requirements.txt

# Run the Streamlit simulator
streamlit run streamlit_app.py
```

### Web Dashboard (Local)

```bash
cd web
npm install
npm run dev
```

Open http://localhost:5173

## 📁 Project Structure

```
├── baseline/
│   ├── figures/figures/     # All the matplotlib visualizations
│   ├── models/models/       # Trained PCA and K-Means models
│   └── metrics/metrics/     # Evaluation results (CSV)
├── web/
│   └── src/                 # React web dashboard source
├── src/                     # Python analysis modules
├── streamlit_app.py         # Interactive simulator
└── README.md                # You are here
```

## 🛠️ Technologies

- **Python**: NumPy, Pandas, Scikit-learn, Matplotlib, Plotly
- **Web**: React, Vite, Chart.js
- **Deployment**: Vercel (web), Streamlit Cloud (simulator)

## 💡 Key Insights

1. **Energy patterns are about timing, not totals** - When you use energy matters more than how much
2. **Three clear groups emerge** - Midday users, evening users, and flat-profile users
3. **PCA dramatically simplifies analysis** - 51 features → 14 components with minimal information loss
4. **Patterns are stable** - Clusters remain consistent across different random seeds

## 🎓 What You Can Learn

- How to apply PCA for dimensionality reduction
- K-Means clustering for pattern discovery
- Feature engineering for time-series data
- Model evaluation and validation
- Building interactive data dashboards
- Deploying ML visualizations

## 📚 Academic Context

This analysis is inspired by real-world energy studies but uses synthetic data for transparency and reproducibility. The methodology follows established practices in load profiling research:

- Feature engineering based on domain knowledge
- Pre-registered analysis plan (no p-hacking)
- Multiple validation metrics
- Clear documentation of limitations

## ⚠️ Limitations

- **Synthetic data** - Generated with known patterns for validation, not real households
- **Single time window** - 30 days, not seasonal variations
- **No external factors** - Weather, pricing, or demographics not included
- **Descriptive, not predictive** - Shows patterns, doesn't forecast future usage

## 🤝 Contributing

Found a bug? Have an idea? Open an issue or submit a pull request!

## 📄 License

MIT License - feel free to use this project for learning or research.

## 📬 Contact

Questions? Feedback? Open an issue on GitHub!

---

**Made with ❤️ for data science education**

Last updated: August 2026
