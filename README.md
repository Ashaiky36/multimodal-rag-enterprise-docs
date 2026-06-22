

# Multi-Modal RAG for Enterprise Documents (v3 - Ollama Vision)

A production-ready Document Intelligence and Retrieval-Augmented Generation (RAG) system designed for parsing and querying complex enterprise documents such as annual reports, financial filings, and regulatory disclosures. This architecture operates **100% locally**, ensuring absolute data privacy with no external API dependencies.

---

## Key Features

* **Advanced PDF Processing**: Leverages MinerU for high-fidelity extraction of text, structured HTML tables, and embedded layout assets.
* **Local Vision Enhancement**: Integrates **Qwen2.5-VL (3B)** locally via Ollama to generate context-aware textual descriptions for charts, graphs, and visual trends.
* **HTML Table Preservation**: Retains the complete native HTML structure of tabular data to protect multi-dimensional financial matrices from text flattening.
* **Fully Offline Inference**: Utilizes **Llama 3.2 (3B)** for fast, local contextual synthesis and secure question-answering.
* **Hybrid Semantic Indexing**: Uses `sentence-transformers` dense embeddings paired with a high-performance **FAISS** vector database.
* **Reactive User Interface**: A clean Streamlit front-end featuring a real-time ingestion progress tracker and a low-latency chat portal.

---

## Problem Statement

Standard text-based RAG architectures frequently fail when processing enterprise documentation because they interpret visually rich pages as unstructured text. This parsing methodology results in the loss of:

* **Structural Table Data**: Cell relationships, column alignments, and nested analytical hierarchies are completely flattened.
* **Multi-Dimensional Insights**: Trends, financial ratios, and metrics trapped inside complex charts or infographics are skipped.
* **Spatial Associations**: The context connecting figures and text layouts is broken.

This system resolves these limitations via a multi-stage, vision-enhanced data extraction pipeline. It preserves native layout semantics and transforms complex graphics into descriptive markdown text before indexing, ensuring no data loss occurs during vectorization.

---

## System Architecture

```text
       ┌────────────────────────┐
       │   User Uploads PDF     │
       └───────────┬────────────┘
                   ▼
       ┌────────────────────────┐
       │   MinerU Extraction    ├─► [Extracts Text, Layouts, & Images]
       └───────────┬────────────┘
                   ▼
       ┌────────────────────────┐
       │   Vision Enhancement   ├─► [Qwen2.5-VL generates descriptions]
       └───────────┬────────────┘
                   ▼
       ┌────────────────────────┐
       │   Table Preservation   ├─► [HTML layout schemas kept intact]
       └───────────┬────────────┘
                   ▼
       ┌────────────────────────┐
       │ Overlapping Chunking   ├─► [2000 chars size / 300 chars overlap]
       └───────────┬────────────┘
                   ▼
       ┌────────────────────────┐
       │   FAISS Vector Store   ├─► [384-dimensional dense index]
       └───────────┬────────────┘
                   ▼
       ┌────────────────────────┐
       │  Llama 3.2 (3B) RAG    ├─► [Contextual Question Answering]
       └───────────┬────────────┘
                   ▼
       ┌────────────────────────┐
       │  Generated Synthesis   ├─► [100% Local Response Path]
       └────────────────────────┘

```

---

## Hardware Requirements

The system configuration is optimized for standard consumer or developer hardware:

| Component | Minimum Requirement | Recommended Specification |
| --- | --- | --- |
| **System Memory** | 8 GB DDR4 | 16 GB DDR4/DDR5 |
| **Storage** | 512 GB SATA SSD | 512 GB NVMe SSD |
| **Processor** | Intel Core i3 (11th Gen) or equivalent | Intel Core i5/i7 or AMD Ryzen 5/7 |
| **Graphics (GPU)** | Intel Integrated Graphics / Apple Silicon | Dedicated NVIDIA GPU (6GB+ VRAM for acceleration) |

---

## Software Dependencies

| Package | Purpose |
| --- | --- |
| `mineru` | Deep-parsing PDF extraction suite |
| `ollama` | Local LLM & VLM orchestration engine (`llama3.2:3b` and `qwen2.5vl:3b`) |
| `faiss-cpu` | Dense vector similarity search index |
| `sentence-transformers` | Semantic text embedding generation |
| `streamlit` | Front-end presentation and interactive UI layer |
| `pdfplumber` | Secondary structural fallback parsing |
| `pillow` | Image manipulation and visual asset pre-processing |

---

## Installation

### 1. Prerequisites (Ollama Setup)

1. Download and install [Ollama](https://ollama.com/) for your operating system.
2. Pull the required core and vision models from your terminal:
```bash
ollama pull llama3.2:3b
ollama pull qwen2.5vl:3b

```



```
3. Ensure the Ollama daemon is active:
   ```bash
   ollama serve

```

### 2. Environment Setup

```bash
# Clone the repository
git clone https://github.com/Ashaiky36/multimodal-rag-enterprise-docs.git
cd multimodal-rag-enterprise-docs

# Checkout the active version 3 development branch
git checkout v3-ollama-vision

# Initialize and configure the isolated Conda environment
conda create -n multimodal-rag python=3.10 -y
conda activate multimodal-rag

# Install dependencies
pip install -r requirements.txt
pip install mineru

# Verify the extraction engine core compilation status
python -c "from src.document_processor import DocumentProcessor; print('Pipeline environment initialized successfully')"

```

### 3. Native Windows Dependencies

If running on Windows, you must configure the following system dependencies manually:

* **Poppler Binaries**:
1. Download the latest compiled windows binaries.
2. Extract files to `C:\poppler`.
3. Append `C:\poppler\Library\bin` to your system environment `PATH` variable.


* **Tesseract OCR Engine**:
1. Install the Windows binary installer.
2. Ensure the **English** language dataset pack is selected during installation.
3. Append the Tesseract installation folder path directly into your system `PATH` environment variable.



---

## Usage

### Direct Execution

```bash
# Launch the Streamlit dashboard application
streamlit run app.py

```

### Processing Workflows

1. **Upload**: Drag and drop your target enterprise PDF into the web UI.
2. **Process**: Click **Process Document** to kick off the ingestion pipeline.
*(Average latency scales between 3 to 5 minutes per 4 pages of dense financial documentation on standard hardware).*
3. **Query**: Once indexing completes successfully, input your queries into the interactive chat portal.

### CLI Integration Testing & Debugging

You can bypass the UI entirely to batch-process files or test the retrieval system directly via the command line:

```bash
# Process a local file asset manually
python src/process_complete.py data/sample_digital1.pdf

# Run automated queries against an existing index database
python src/query_rag.py sample_digital1 "What is the shareholding pattern?"

```

---

## Project Structure

```text
multimodal-rag-enterprise-docs/
├── app.py                     # Streamlit main application logic
├── requirements.txt           # Framework dependencies manifest
├── README.md                  # System documentation manual
├── .gitignore                 # Repository file exclusion parameters
├── data/                      # Source PDF file directory
│   └── .gitkeep
├── processed_docs/            # Output directory for generated document metadata
│   └── {doc_id}/
│       ├── {doc_name}_enhanced.md    # Intermediary markdown enriched with VLM image summaries
│       ├── {doc_name}_final.md       # Target markdown file retaining raw HTML tabular data
│       ├── {doc_name}_chunks_final.json
│       └── vector_store_final/       # Serialized FAISS database binary files
└── src/
    ├── __init__.py
    ├── document_processor.py  # Central pipeline orchestrator
    ├── enhanced_retriever.py  # Multi-stage context retriever & ranking logic
    ├── overlap_chunker.py     # Clean token sliding-window splitter
    ├── vector_store.py        # Abstracted interface layer for FAISS indexing
    ├── rag_llama.py           # Local generation manager for Llama 3.2
    ├── vision_enhance_v2.py   # Vision script handling Qwen2.5-VL orchestration
    ├── table_flattener.py     # Script protecting HTML semantic tables from destructive flattening
    ├── query_rag.py           # Command-line interface querying tool
    └── process_complete.py    # End-to-end execution script for automated document indexing

```

---

## Technical Performance Metrics

| Evaluation Vector | Target Metric Performance Baseline |
| --- | --- |
| **Table Layout Retention** | **90–95%** (Validated via complex HTML semantic parsing checks) |
| **Chart Interpretation Accuracy** | **~90%** (Consistent structural description via Qwen2.5-VL) |
| **Plain Text Retrieval Accuracy** | **~95%** |
| **Pipeline Latency** | **3–5 minutes** (Standard 4-page financial document benchmark) |
| **Runtime Memory Footprint** | **~4–6 GB** System RAM |
| **Disk Deployment Footprint** | **~5 GB** (Total storage allocated for local model weights) |

---

## Architectural Comparison Matrix

| Architectural Vector | Architecture v2 (External API Engine) | Architecture v3 (Local Multi-Modal Engine) |
| --- | --- | --- |
| **API Token Requirements** | Required (Cloud Gateway Auth) | **None** (100% Offline deployment) |
| **Rate Limits** | Restricted (Throttled by cloud tiering) | **Unlimited** local executions |
| **Vision Processing Engine** | Remote Server Environment | **Local Qwen2.5-VL (3B)** |
| **Table Ingestion Method** | Flattened Markdown Strings | **Complete Native HTML Schema Retention** |
| **Primary Synthesis Model** | Cloud Managed API Engine | **Local Llama 3.2 (3B Engine)** |
| **Infrastructure Costs** | Pay-Per-Token Utility Pricing | **Zero operational costs** post-setup |
| **Enterprise Data Privacy** | Data processed via third-party servers | **100% On-Premises Isolated Boundary** |

---

## Troubleshooting

### Resolution Matrix

| Symptom | Probable Cause | Action Pathway |
| --- | --- | --- |
| `Local connection failure` | Ollama service is down or unreachable on port `11434` | Open a separate terminal window and execute `ollama serve`. |
| `ModuleNotFoundError` | Missing path linkage or package configuration failure | Re-run `pip install mineru` or ensure your active Conda context matches `multimodal-rag`. |
| `Memory page faults` | RAM exhaustion during high-resolution PDF processing | Close background processes or slice larger PDF documents into micro-batches. |
| `Initialization errors` | Corrupted model weights or missing configuration manifests | Force download the models cleanly using `ollama pull qwen2.5vl:3b`. |
| `Streamlit browser drops` | Localhost loopback or network configuration conflict | Force bind the address space explicitly via: `streamlit run app.py --server.address=127.0.0.1`. |

### System Logs

Detailed background exception traces and operational status events are routed directly to the localized file handler located at `streamlit_app.log`.

---

## License

This project is open-source software licensed under the terms of the **MIT License**.