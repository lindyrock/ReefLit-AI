# ---------- ReefLit AI • Streamlit dashboard image ----------
    FROM python:3.11-slim

    # 1. System deps
    RUN apt-get update && apt-get install -y --no-install-recommends \
            build-essential gcc git && \
        rm -rf /var/lib/apt/lists/*
    
    # 2. Create app dir & copy minimal files
    WORKDIR /app
    COPY requirements.txt .          # if you have one
    COPY environment.yml  .          # fallback
    COPY src/      src/
    COPY config/   config/
    COPY index/    index/
    COPY data/     data/
    
    # 3. Install Python deps (use pip for speed)
    # Either use requirements.txt or pip-install from environment.yml
    RUN pip install -U pip && \
        if [ -f requirements.txt ]; then \
            pip install -r requirements.txt; \
        else \
            pip install streamlit sentence-transformers faiss-cpu plotly pyyaml; \
        fi
    
    # 4. Expose port & cmd
    ENV PORT 8080
    EXPOSE 8080
    CMD ["streamlit", "run", "src/dashboard.py", "--server.port", "8080", "--server.address", "0.0.0.0", "--server.enableCORS", "false"]
    