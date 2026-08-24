# Deployment Guide

## Architecture

The Energy Clustering Analysis application is a full-stack system with three main components:

```
┌─────────────────┐
│  React/Next.js  │ (Vercel) - Frontend, landing page, visualizations
│  + Three.js     │
└────────┬────────┘
         │
    ┌────┴─────────────┐
    │                  │
┌───▼────────┐   ┌────▼──────────┐
│  Flask API │   │   Streamlit    │
│ (Backend)  │   │  (Simulator)   │
└────────────┘   └────────────────┘
```

## Prerequisites

- Node.js 18+
- Python 3.9+
- Git
- Vercel CLI (for deployment)

## Local Development

### 1. Frontend (Next.js + React)

```bash
cd web
npm install
npm run dev
```

Open http://localhost:3000

### 2. Backend (Flask API)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
cd backend
pip install -r requirements.txt
python app.py
```

API runs on http://localhost:5000

### 3. Simulator (Streamlit)

```bash
cd ..
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Simulator runs on http://localhost:8501

## Production Deployment

### Vercel Deployment (Next.js Frontend)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel deploy

# For production
vercel deploy --prod
```

**Environment variables on Vercel:**
- `NEXT_PUBLIC_API_URL`: Backend API URL (e.g., https://api.yourdomain.com)
- `STREAMLIT_URL`: Streamlit service URL (optional, for local demo)

### Backend Deployment

#### Option 1: Render.com (Recommended)

1. Push code to GitHub
2. Create new Web Service on Render
3. Connect GitHub repository
4. Set Build Command: `pip install -r backend/requirements.txt`
5. Set Start Command: `gunicorn -w 4 -b 0.0.0.0:$PORT backend.app:app`
6. Deploy

#### Option 2: Railway

```bash
railway init
railway add
railway up
```

#### Option 3: AWS Lambda + API Gateway

Package the Flask app with Zappa:

```bash
pip install zappa
zappa init
zappa deploy production
```

#### Option 4: Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY baseline ./baseline
COPY backend ./backend

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "backend.app:app"]
```

Deploy with:
```bash
docker build -t energy-api .
docker run -p 5000:5000 energy-api
```

### Streamlit Deployment

#### Streamlit Community Cloud (Easiest)

1. Push repo to GitHub
2. Go to https://share.streamlit.io
3. Connect GitHub repo
4. Select `streamlit_app.py`
5. Deploy

#### Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## Environment Configuration

### Vercel Environment Variables

```env
# Frontend (.env.local)
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_STREAMLIT_URL=https://simulator.yourdomain.com
```

### Backend Environment Variables

```env
# backend/.env
FLASK_ENV=production
FLASK_DEBUG=False
CORS_ORIGINS=https://yourdomain.com
```

## Performance Optimization

### Frontend
- Image optimization via Next.js
- Code splitting and lazy loading
- CSS optimization (Tailwind CSS purging)
- Compression enabled by default

### Backend
- Gunicorn worker pool (4 workers)
- Redis caching for API responses
- Connection pooling
- Gzip compression

### Database
- Model caching in memory
- Vectorized NumPy operations
- Efficient data structures

## Monitoring

### Frontend (Vercel Analytics)
- Core Web Vitals
- Performance metrics
- Error tracking

### Backend
```python
# Add monitoring endpoints
@app.route('/api/health')
def health():
    return {'status': 'ok', 'timestamp': datetime.now()}

@app.route('/api/metrics')
def metrics():
    # Return Prometheus metrics
    pass
```

## Troubleshooting

### 502 Bad Gateway
- Check backend service is running
- Verify environment variables
- Check CORS configuration
- Monitor logs: `vercel logs`

### Slow API Responses
- Enable caching headers
- Check database connection
- Profile with Python profiler
- Consider async processing

### Memory Issues
- Monitor model loading
- Use lazy loading for large files
- Clear temporary data
- Enable compression

## Maintenance

### Regular Updates
```bash
# Update dependencies
npm outdated  # in web/
pip list --outdated  # in backend/

# Update and commit
npm update
pip install --upgrade -r requirements.txt
```

### Database Backups
- Models stored in `baseline/models/`
- Ensure Git LFS if files > 100MB
- Regular repository backups

### Log Monitoring
```bash
# Vercel logs
vercel logs

# Backend logs
tail -f backend/app.log
```

## CI/CD Pipeline

Example GitHub Actions workflow:

```yaml
name: Deploy

on:
  push:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: cd web && npm ci && npm run build
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: vercel/action@master
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
```

## Support

For issues or questions:
1. Check GitHub Issues
2. Review logs: `vercel logs`, Flask logs
3. Test locally first
4. Create detailed bug report with reproduction steps
