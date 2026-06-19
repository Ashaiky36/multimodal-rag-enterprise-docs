FROM python:3.11-slim

# Set system envs to keep Python output clean and predictable
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HF_HUB_ENABLE_HF_TRANSFER=1 \
    OLLAMA_HOST=0.0.0.0 \
    OLLAMA_ORIGINS="*"

WORKDIR /app

# Step 1: Install underlying Linux rendering layers & tools
RUN apt-get update && apt-get install -y \
    build-essential \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-hin \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    git \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Step 2: Install Ollama (for local LLM and vision models)
RUN curl -fsSL https://ollama.com/install.sh | sh

# Step 3: Install Python dependencies cleanly from requirements manifest
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Step 4: Install MinerU (with all dependencies)
RUN pip install mineru

# Step 5: Verify MinerU installation
RUN mineru --help || true

# Step 6: Pre-download Ollama models (optional - uncomment if you want to bake models into image)
# Warning: This will increase image size significantly (~5GB)
# RUN ollama serve & sleep 5 && \
#     ollama pull llama3.2:3b && \
#     ollama pull qwen2.5vl:3b && \
#     ollama stop

# Step 7: Create application runtime directories
RUN mkdir -p processed_docs outputs logs data

# Step 8: Copy the rest of your local RAG application code
COPY . .

# Step 9: Create entrypoint script for Ollama + Streamlit
RUN echo '#!/bin/bash\n\
# Start Ollama in background\n\
ollama serve &\n\
\n\
# Wait for Ollama to be ready\n\
echo "Waiting for Ollama to start..."\n\
sleep 10\n\
\n\
# Check if models are available, pull if not\n\
if ! ollama list | grep -q "llama3.2:3b"; then\n\
    echo "Pulling llama3.2:3b..."\n\
    ollama pull llama3.2:3b\n\
fi\n\
\n\
if ! ollama list | grep -q "qwen2.5vl:3b"; then\n\
    echo "Pulling qwen2.5vl:3b..."\n\
    ollama pull qwen2.5vl:3b\n\
fi\n\
\n\
# Start Streamlit\n\
streamlit run app.py --server.port=8501 --server.address=0.0.0.0\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Expose Streamlit application port
EXPOSE 8501

# Expose Ollama API port (optional, for debugging)
EXPOSE 11434

# Run the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]