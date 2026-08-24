# Energy Consumption Pattern Analysis

A modern full-stack web application for analyzing and visualizing energy consumption patterns using PCA and K-Means clustering.

## 🎯 Overview

This project demonstrates:
- **Statistical Analysis**: PCA for dimensionality reduction, K-Means for clustering
- **Data Science**: 200 consumers, 30 days, 144,000 records analyzed
- **Interactive Visualization**: 3D cluster explorer, hourly profiles, real-time animations
- **Modern Web Stack**: React/Next.js frontend with Three.js, Flask backend, Streamlit simulator

## 🏗️ Architecture

### Frontend (React/Next.js)
- **3D Visualization**: Interactive Three.js cluster explorer
- **Data Viewers**: Hourly consumption charts, dataset explorer
- **Animations**: Profile playback, scroll-triggered narrative cards
- **Export**: CSV, JSON, text report formats
- **Responsive**: Mobile-first design with dark theme

### Backend (Flask)
- **Model Serving**: PCA and K-Means model inference
- **API**: RESTful endpoints for clustering analysis
- **Plot Generation**: Matplotlib visualizations served as PNG/base64
- **CORS Enabled**: Safe cross-origin requests

### Simulator (Streamlit)
- **Interactive Dashboard**: Parameter adjustment, live updates
- **3 Pages**: Overview, Dataset inspection, Cluster visualization
- **Charts**: Plotly visualizations with dark theme
- **No Popups**: Cleaned UI focused on data

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/shaxntanu/Energy-Consumption-Pattern-Analysis-using-PCA-and-K-Means.git
cd Energy-Consumption-Pattern-Analysis-using-PCA-and-K-Means
```

### 2. Frontend
```bash
cd web
npm install
npm run dev
```
Open http://localhost:3000

### 3. Backend API
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
cd backend
pip install -r requirements.txt
python app.py
```
API: http://localhost:5000

### 4. Streamlit Simulator
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```
Simulator: http://localhost:8501

## 📊 Data & Analysis

### Dataset
- **Consumers**: 200
- **Duration**: 30 days, hourly readings
- **Records**: 144,000 data points
- **Features**: 51 (hourly + time-based)
- **Synthetic**: Generated with known archetypes for validation

### Methodology
1. **Standardization**: Zero mean, unit variance
2. **PCA**: 14 components, 95% variance retention
3. **K-Means**: K=3, selected via pre-registered rule
4. **Metrics**: Silhouette, Calinski-Harabasz, Davies-Bouldin, Gap Statistic

### Results: Three Clusters

| Cluster | Consumers | Peak Hour | Peak Value | Pattern |
|---------|-----------|-----------|------------|---------|
| **Midday-Peaking** | 94 (47%) | 1 PM | 3200 kWh | Rises through morning to afternoon plateau |
| **Flat All-Day** | 57 (28%) | 7 PM | 2620 kWh | Steady throughout day, weak evening peak |
| **Evening-Peaking** | 49 (25%) | 8 PM | 3800 kWh | Quiet by day, sharp peak near dark |

## 🎨 Features

### 3D Visualization
- Interactive Three.js cluster explorer
- Mouse drag rotation, zoom, responsive
- 200 consumer points colored by cluster
- 3 cluster spheres with grid reference

### Data Exploration
- Hourly consumption patterns by cluster
- Dataset viewer with tabbed cluster selection
- Peak hour, usage statistics
- Interactive bar charts

### Profile Playback
- 24-hour animation with play/pause controls
- Adjustable speed (0.5x to 3x)
- Real-time consumption values
- Hour slider for manual navigation

### Cluster Comparison
- Multi-metric dashboard (size, usage, peak, flatness, variance)
- Comparative bar charts
- Statistical summary table
- Cluster insights cards

### Export Data
- **CSV**: Cluster stats + hourly profiles (spreadsheet-ready)
- **JSON**: Complete dataset with metadata (for integration)
- **Text**: Methodology & findings summary (for docs)

## 🌐 Deployment

### Vercel (Frontend)
```bash
npm i -g vercel
vercel deploy --prod
```

### Backend Options
- **Render.com**: Easiest (git push deploy)
- **Railway**: Quick setup
- **AWS Lambda**: Serverless
- **Docker**: Any platform

### Streamlit Cloud
1. Push to GitHub
2. Connect at https://share.streamlit.io
3. Auto-deploys on push

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

## 📁 Project Structure

```
.
├── web/                        # React/Next.js frontend
│   ├── app/
│   │   ├── page.tsx           # Main landing page
│   │   ├── components/        # React components
│   │   ├── api/               # API routes
│   │   ├── lib/               # Utilities (a11y, performance)
│   │   └── globals.css        # Dark theme CSS
│   ├── package.json
│   └── next.config.js
├── backend/                    # Flask API
│   ├── app.py                 # Main Flask app
│   ├── plot_service.py        # Matplotlib plots
│   └── requirements.txt
├── baseline/                   # Pre-trained models
│   ├── models/                # PKL files (PCA, K-Means, scaler)
│   ├── metrics/               # CSV evaluation metrics
│   ├── reports/               # Analysis reports
│   └── figures/               # Generated charts
├── streamlit_app.py           # Streamlit simulator
├── src/                        # Python analysis modules
│   ├── preprocessing.py
│   ├── feature_engineering.py
│   ├── pca_analysis.py
│   ├── clustering.py
│   ├── evaluation.py
│   └── dashboard_*.py
├── DEPLOYMENT.md              # Deployment guide
└── README.md                  # This file
```

## 🔧 Technologies

### Frontend
- **React 19** - UI library
- **Next.js 16.3** - React framework
- **Three.js** - 3D graphics
- **@react-three/fiber** - React Three.js
- **Tailwind CSS 4** - Styling
- **TypeScript** - Type safety

### Backend
- **Flask 3.0** - Web framework
- **NumPy & Scikit-learn** - Data science
- **Matplotlib** - Visualization
- **Gunicorn** - Production server
- **Flask-CORS** - Cross-origin support

### Data Science
- **PCA**: Dimensionality reduction (scikit-learn)
- **K-Means**: Clustering (scikit-learn)
- **Evaluation**: Silhouette, Gap, Davies-Bouldin scores
- **Plotting**: Plotly, Matplotlib

## ✨ Highlights

### Performance
- ⚡ Next.js auto-optimization
- 🗜️ Gzip compression enabled
- 📦 Code splitting & lazy loading
- 🎯 Web Vitals monitoring
- ⚙️ Model caching for fast inference

### Accessibility
- ♿ WCAG compliance focus
- 🎯 Screen reader support
- ⌨️ Full keyboard navigation
- 🎨 High contrast dark theme
- 📱 Responsive design

### Quality
- 🧪 Type-safe TypeScript throughout
- 📊 Reproducible methodology
- 🔍 Pre-registered analysis plan
- 📈 Comprehensive metrics

## 📚 Resources

- [Deployment Guide](DEPLOYMENT.md)
- [Data Analysis Report](baseline/reports/cluster_insights.csv)
- [Model Metrics](baseline/metrics/evaluation_metrics.csv)
- [Generated Visualizations](baseline/figures/figures/)

## 📝 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- Energy consumption data patterns inspired by real-world studies
- Three.js community for 3D visualization
- Vercel for deployment infrastructure
- Streamlit for interactive analysis tools

## 📮 Contact

For questions or collaboration:
- Create an Issue on GitHub
- Submit a Pull Request
- Check the [DEPLOYMENT.md](DEPLOYMENT.md) for troubleshooting

---

**Last Updated**: August 2026 | **Status**: Production Ready ✅
