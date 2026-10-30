# The interpreter the analysis is tested on. Every pin in requirements.txt ships a
# cp314 manylinux wheel, so the image builds without a compiler.
FROM python:3.14-slim

WORKDIR /app

# libgomp1 is OpenMP, which scikit-learn's K-Means links against. Without it the
# import fails at runtime rather than at build time.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Use a fixed unprivileged UID; no passwd package is needed in the slim image.
RUN mkdir -p /home/app && chown 10001:10001 /home/app
ENV HOME=/home/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=10001:10001 . .

USER 10001:10001

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
