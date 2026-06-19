```markdown
# Multi-Modal RAG for Enterprise Documents (v3 - Ollama Vision)

A production-ready document intelligence and retrieval-augmented generation (RAG) system designed for complex enterprise documents such as annual reports, financial filings, and regulatory disclosures. This architecture operates entirely locally, requiring no external API keys or cloud dependencies.

---

## Key Features

* **PDF Processing**: MinerU-based extraction providing high accuracy for text, structured tables, and embedded charts.
* **Vision Enhancement**: Integrated Qwen2.5VL (3B) local vision model for automated chart, graph, and asset descriptions.
* **HTML Table Preservation**: Retains complete structural integrity of tables to facilitate accurate contextual retrieval and prevent data loss from text flattening.
* **Local Large Language Model**: Utilizes Llama 3.2 (3B) for secure, fully offline contextual question answering.
* **Semantic Search**: FAISS vector database coupled with sentence-transformers embeddings for high-precision document indexing.
* **Real-time User Interface**: Built with Streamlit to deliver live processing status updates and an interactive query portal.
* **Unified Environment**: Standardized configuration within a single Conda environment to avoid cross-dependency conflicts.

---

## Problem Statement

Standard text-based RAG architectures frequently fail when processing enterprise documentation because they interpret visually rich pages as unstructured text. This parsing methodology results in the loss of:

* Structural table data (cell relationships, rows, columns, and analytical hierarchies).
* Multi-dimensional insights contained within charts, trends, and financial graphics.
* Spatial and visual contextual associations.

This system resolves these limitations via a multi-stage data extraction pipeline. It preserves native structural layouts and leverages vision-language models to transform graphics into descriptive text before vectorization and database indexing.

---

## System Architecture


```

User Uploads PDF
↓
MinerU Extraction (Text, HTML Tables, and Structural Images)
↓
Vision Enhancement (Qwen2.5VL generates descriptions for charts/tables)
↓
Table Preservation (HTML layout schemas are kept intact)
↓
Overlapping Chunk Generation (2000 character size, 300 character overlap)
↓
FAISS Vector Store Initialization (384-dimensional embeddings)
↓
Llama 3.2 (3B) Core Execution for RAG Q&A
↓
Generated Synthesis (Fully local execution path)

```

---

## Hardware Requirements

The system configuration is optimized for standard, non-industrial hardware profiles:

| Component | Minimum Requirement | Recommended Specification |
|:---|:---|:---|
| **System Memory** | 8 GB DDR4 | 16 GB DDR4/DDR5 (for extensive documents) |
| **Storage Infrastructure** | 512 GB Solid State Drive (SSD) | 512 GB NVMe SSD |
| **Processor** | Intel Core i3 11th Gen (or equivalent) | Intel Core i5/i7 or AMD Ryzen 5/7 |
| **Graphics Processing Unit** | Intel Integrated Graphics | Dedicated NVIDIA GPU (for accelerated vision tasks) |

---

## Software Dependencies

| Package | Purpose |
|:---|:---|
| `mineru` | Primary deep-parsing PDF extraction suite |
| `ollama` | Local LLM orchestration engine (Llama 3.2 and Qwen2.5VL) |
| `faiss-cpu` | Dense vector similarity search database |
| `sentence-transformers` | Semantic text embedding generation |
| `streamlit` | Front-end web presentation layer |
| `pdfplumber` | Secondary fallback parsing framework |
| `pillow` | Image manipulation and pre-processing |

A comprehensive dependency manifest is located in the `requirements.txt` file.

---

## Installation

### Prerequisites

1. Download and configure the Ollama runtime platform for your operating system.
2. Pull the required models via the command-line interface:
   ```bash
   ollama pull llama3.2:3b
   ollama pull qwen2.5vl:3b

```

3. Initialize the background service instance:
```bash
ollama serve

```



### Setup Sequence

```bash
# Clone the target repository
git clone [https://github.com/Ashaiky36/multimodal-rag-enterprise-docs.git](https://github.com/Ashaiky36/multimodal-rag-enterprise-docs.git)
cd multimodal-rag-enterprise-docs

# Checkout the active version 3 development branch
git checkout v3-ollama-vision

# Initialize and configure the isolated Conda virtual environment
conda create -n multimodal-rag python=3.10 -y
conda activate multimodal-rag

# Install core framework dependencies
pip install -r requirements.txt

# Install the MinerU data extraction pipeline
pip install mineru

# Verify compilation status
python -c "import mineru; print('MinerU installed successfully')"

```

### System Dependencies (Windows Environment)

1. **Poppler Binaries**:
* Secure the latest package release from the repository resources.
* Extract files to the target path: `C:\poppler`
* Append the system environment variables PATH configuration to include: `C:\poppler\Library\bin`


2. **Tesseract OCR Engine**:
* Install the latest binaries.
* Ensure English language support data packs are selected during setup.
* Append the execution path directly into the system environment PATH variables.



---

## Usage

### Direct Invocation

```bash
# Ensure the local model service is active
ollama serve

# Execute the Streamlit presentation layer
streamlit run app.py

```

### Processing Workflows

1. Upload the target document via the file upload interface component.
2. Select **Process Document** to initiate the multi-stage ingestion sequence.
3. Allow the pipeline to finish execution (approximate latency of 3 to 5 minutes per 4-page financial document block).
4. Input complex cross-sectional inquiries into the chat prompt once indexed.

### Ingestion Sequence Pipeline Metrics

The user interface logs processing state progress across the following programmatic intervals:

1. Processing step: MinerU extraction (Text parsing, structural table mapping, image capturing)
2. Processing step: Vision synthesis (Qwen2.5VL chart evaluation and contextual tagging)
3. Processing step: Tabular normalization (Preserving comprehensive HTML DOM matrix definitions)
4. Processing step: Token chunk creation (Windowing configuration with explicit overlaps)
5. Processing step: Datastore creation (FAISS localized vector file builds)
6. State active: Evaluation pipeline ready for system queries

### Local Integration Verification Testing

```bash
# Process a local file asset manually
python src/process_complete.py data/sample_digital1.pdf

# Run automated queries against the index database
python src/query_rag.py sample_digital1 "What is the shareholding pattern?"

```

---

## Project Structure

```
multimodal-rag-enterprise-docs/
├── app.py                    # Streamlit main application logic
├── requirements.txt          # Framework dependencies manifest
├── README.md                 # System documentation manual
├── .gitignore                # Repository file exclusion parameters
├── data/                     # Source PDF file directory
│   └── .gitkeep
├── processed_docs/           # Directory for generated document metadata
│   └── {doc_id}/
│       ├── {doc_name}_enhanced.md    # Markdown file populated with vision metrics
│       ├── {doc_name}_final.md       # Target markdown file retaining HTML tabular data
│       ├── {doc_name}_chunks_final.json
│       └── vector_store_final/       # FAISS database binary files
└── src/
    ├── __init__.py
    ├── document_processor.py  # Orchestration module for processing pipelines
    ├── enhanced_retriever.py  # Core search algorithm and data integration logic
    ├── overlap_chunker.py     # String parsing and document chunk windowing
    ├── vector_store.py        # Abstracted interface layer for FAISS indexing
    ├── rag_llama.py           # Local generation management for Llama models
    ├── vision_enhance_v2.py   # Analytical logic processing for Qwen2.5VL
    ├── table_flattener.py     # Component for HTML semantic matrix preservation
    ├── query_rag.py           # Command-line interface querying module
    └── process_complete.py    # Sequential end-to-end processing execution script

```

---

## System Performance Matrix

| Evaluation Vector | Operational Efficiency Metric |
| --- | --- |
| **Table Layout Accuracy** | 90-95% (Validation based on full HTML semantic structure preservation) |
| **Chart Interpretation Performance** | Approximately 90% (Qwen2.5VL descriptive matching accuracy) |
| **Plain Text Retrieval Accuracy** | Approximately 95% |
| **System Processing Latency** | 3-5 minutes (Standardized 4-page enterprise document baseline) |
| **Execution Memory Utilization** | Approximately 4-6 GB System RAM |
| **Disk Deployment Footprint** | Approximately 5 GB (Total storage allocated for local weights) |

---

## Troubleshooting

### Matrix of Common Operational Issues

| Error Encountered | Diagnostic Verification | Resolution Action Pathway |
| --- | --- | --- |
| Local connection failure | Ollama services unreachable on standard ports | Execute `ollama serve` within a separate administrative terminal context |
| Dependency errors | Module reference missing for execution path | Re-run `pip install mineru` or utilize native system `magic-pdf` calls |
| Memory page faults | Allocation limitations reached during deep document analysis | Terminate extraneous software processes; split document blocks into micro-batches |
| Initialization errors | Vision parameters throw invalid configuration warnings | Re-index local model manifests explicitly with `ollama pull qwen2.5vl:3b` |
| UI browser drops | Streamlit interface network loop disruptions | Re-initialize presentation layer mapping explicitly via: `streamlit run app.py --server.address=127.0.0.1` |

### System Logs

Review the localized application event logging output file (`streamlit_app.log`) to diagnose core error events.

---

## Architectural Comparison Matrix

| Structural Vector | Architecture v2 (External API Engine) | Architecture v3 (Local Multi-Modal Engine) |
| --- | --- | --- |
| **API Token Requirements** | Mandated (External Gateway Authentication) | Unnecessary (Fully Local Environment Deployment) |
| **Transaction Rate Caps** | Explicit (Throttled at 20 Requests Per Day) | Unlimited Execution Frequency |
| **Vision Model Infrastructure** | Remote Server Execution Environment | Local Qwen2.5VL (3B Variable Parameters) |
| **Tabular Structural Methods** | Simplified Flat-String Markdown Serialization | Complete Native HTML Preservation Schema |
| **Primary LLM Generation** | Remote Cloud Managed API Processing | Localized Llama 3.2 (3B Processing Engine) |
| **Infrastructure Overhead Cost** | Standard Tiers Subject to Consumption Pricing | Zero Maintenance Cost Post-Deployment |
| **Enterprise Privacy Standard** | Transaction Data Transmitted Internationally | 100% On-Premises Isolated Data Boundary |

---

## License

This software utility is licensed under the terms of the MIT License.

```

```