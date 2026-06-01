# Multi-Modal RAG for Enterprise Documents

A modular document intelligence and retrieval-augmented generation (RAG) system designed for complex enterprise documents such as annual reports, financial filings, and regulatory disclosures. The system extracts and indexes text, tables, charts, and handwritten content from PDFs to enable semantic search and question answering.

## Problem Statement

Standard RAG systems fail on enterprise documents because they treat every page as plain text, losing:

- Table structures (cells, rows, columns, relationships)
- Chart and graph insights
- Handwritten annotations

This system addresses these limitations through a multi-stage extraction pipeline that preserves document structure before vectorisation and retrieval.

## Features

- Text extraction with automatic OCR fallback for scanned PDFs
- Table detection and extraction as structured data (Pandas DataFrames)
- Chart extraction and captioning via vision-language models
- Handwritten text recognition
- Semantic search using FAISS vector database
- Local LLM integration for secure, offline question answering
- Streamlit-based user interface

## System Architecture

The pipeline consists of four main stages:

1. Ingestion: PDF parsing, text extraction (pdfplumber), OCR fallback (Tesseract), table extraction (camelot-py)
2. Enrichment: Chart description generation via local VLM (BakLLaVA), handwriting recognition (EasyOCR)
3. Indexing: Text chunking, embedding generation (sentence-transformers), vector storage (FAISS)
4. Retrieval: Semantic search, context injection, response generation (local LLM)

## Hardware Requirements

The system is optimised for modest hardware:

- RAM: 8 GB DDR4
- Storage: 512 GB SSD
- Processor: Intel i3 11th Gen
- Graphics: Intel Integrated

All models run locally with no GPU requirement.

## Software Dependencies

- Python 3.10
- pdfplumber, pdf2image, camelot-py (PDF processing)
- pytesseract, EasyOCR (OCR and handwriting)
- sentence-transformers (embeddings)
- faiss-cpu (vector database)
- Ollama with phi3:3.8b-mini or qwen2:1.5b (local LLM)
- Streamlit (user interface)

A complete list is available in `requirements.txt`.

## Installation

Clone the repository:

```bash
git clone https://github.com/Ashaiky36/multimodal-rag-enterprise-docs.git
cd multimodal-rag-enterprise-docs