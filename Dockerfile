# ---------- ReefLit AI • Streamlit dashboard ----------
    FROM python:3.11-slim

    # System deps for wheels that need a compiler
    RUN apt-get update && apt-get install -y --no-install-recommends \
            build-essential gcc git && \
        rm -rf /var/lib/apt/lists/*
    
    # Work dir
    WORKDIR /app
    
    # Copy code & download helper (NO data / index)
    COPY src/      src/
    COPY config/   config/
    COPY scripts/  scripts/
    
    # Python deps (no environment.yml here – keep it light)
    RUN pip install -U pip \
        streamlit sentence-transformers faiss-cpu plotly pyyaml requests tqdm
    
    # Streamlit wants a port env
    ENV PORT 8080
    EXPOSE 8080
    
    # Pull latest index/data from GH Actions artifact, then launch Streamlit
    CMD ["/bin/bash", "-c", "python scripts/get_latest_index.py && \
         streamlit run src/dashboard.py \
           --server.port $PORT --server.address 0.0.0.0 --server.enableCORS false"]
    