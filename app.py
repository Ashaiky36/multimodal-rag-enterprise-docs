"""
Premium Corporate Document Intelligence System
Multimodal RAG for Enterprise Annual Reports
"""

import streamlit as st
import os
import sys
import tempfile
import subprocess
import shutil
import time
import hashlib
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

# Import modules
from vector_store import VectorStore
from enhanced_retriever import EnhancedRetriever
from document_processor import DocumentProcessor

# Page configuration
st.set_page_config(
    page_title="Document Intelligence | Corporate RAG",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main { background-color: #f8fafc; }
    [data-testid="stSidebar"] { background-color: #0f172a; padding: 2rem 1rem; }
    [data-testid="stSidebar"] .stMarkdown { color: #e2e8f0; }
    h1, h2, h3 { color: #0f172a; font-weight: 600; }
    .user-message {
        background-color: #eef2ff;
        border-radius: 12px;
        padding: 12px 16px;
        margin: 8px 0;
        border-left: 4px solid #4f46e5;
    }
    .assistant-message {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 12px 16px;
        margin: 8px 0;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #10b981;
    }
    .source-card {
        background-color: #f1f5f9;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
        border-left: 3px solid #6366f1;
        font-size: 0.85rem;
    }
    .footer {
        text-align: center;
        padding: 1.5rem;
        color: #94a3b8;
        font-size: 0.75rem;
        border-top: 1px solid #e2e8f0;
        margin-top: 2rem;
    }
    .status-success { color: #10b981; }
    .status-error { color: #ef4444; }
    .status-warning { color: #f59e0b; }
    .status-info { color: #3b82f6; }
    .status-active { color: #8b5cf6; animation: pulse 1.5s infinite; }
    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize all session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "retriever" not in st.session_state:
        st.session_state.retriever = None
    if "vector_store" not in st.session_state:
        st.session_state.vector_store = None
    if "image_linker" not in st.session_state:
        st.session_state.image_linker = None
    if "current_doc_id" not in st.session_state:
        st.session_state.current_doc_id = None
    if "current_doc_name" not in st.session_state:
        st.session_state.current_doc_name = None
    if "processing_complete" not in st.session_state:
        st.session_state.processing_complete = False
    if "last_uploaded_file_hash" not in st.session_state:
        st.session_state.last_uploaded_file_hash = None
    if "is_processing" not in st.session_state:
        st.session_state.is_processing = False
    if "processor" not in st.session_state:
        st.session_state.processor = DocumentProcessor("processed_docs")
    if "rag" not in st.session_state:
        st.session_state.rag = None
    if "status_messages" not in st.session_state:
        st.session_state.status_messages = []
    if "processing_started" not in st.session_state:
        st.session_state.processing_started = False
    if "pending_upload" not in st.session_state:
        st.session_state.pending_upload = None


init_session_state()


def add_status(msg: str, status: str = "info"):
    """Add a status message."""
    st.session_state.status_messages.append({"msg": msg, "status": status})


def run_processing():
    """Run the actual processing."""
    if not st.session_state.pending_upload:
        return
    
    tmp_path = st.session_state.pending_upload["tmp_path"]
    doc_name = st.session_state.pending_upload["doc_name"]
    file_hash = st.session_state.pending_upload["file_hash"]
    file_name = st.session_state.pending_upload["file_name"]
    
    status_placeholder = st.empty()
    
    def update_status(msg, status="info"):
        add_status(msg, status)
        with status_placeholder.container():
            st.markdown("### 📋 Processing Status")
            for s in st.session_state.status_messages[-10:]:
                icon = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌", "active": "⏳"}.get(s["status"], "•")
                st.markdown(f"{icon} {s['msg']}")
    
    try:
        update_status("Starting document processing...", "info")
        
        # Step 1: MinerU Extraction
        update_status("Step 1: Running MinerU extraction (this may take 2-5 minutes)...", "active")
        mineru_cmd = f"mineru -p {tmp_path} -o processed_docs/{doc_name} -b pipeline"
        result = subprocess.run(mineru_cmd, shell=True, capture_output=True, text=True, timeout=600)
        
        if result.returncode != 0:
            update_status(f"MinerU failed: {result.stderr[:200]}", "error")
            st.session_state.is_processing = False
            st.session_state.processing_started = False
            return
        
        update_status("✅ MinerU extraction complete!", "success")
        
        # Step 2: Find markdown
        doc_folder = Path(f"processed_docs/{doc_name}")
        md_files = list(doc_folder.rglob("*.md"))
        
        if not md_files:
            update_status("❌ No markdown file found", "error")
            st.session_state.is_processing = False
            st.session_state.processing_started = False
            return
        
        update_status(f"✅ Found {len(md_files)} markdown files", "success")
        
        # Step 3: Vision Enhancement
        update_status("Step 2: Running vision enhancement with Qwen2.5VL...", "active")
        
        try:
            from vision_enhance_v2 import VisionEnhancerV2
            enhancer = VisionEnhancerV2(vision_model="qwen2.5vl:3b")
            enhanced = enhancer.enhance_document(doc_folder)
            update_status("✅ Vision enhancement complete!" if enhanced else "⚠️ No images found", "success" if enhanced else "warning")
        except Exception as e:
            update_status(f"⚠️ Vision enhancement warning: {str(e)[:100]}", "warning")
        
        # Step 4: Process tables
        update_status("Step 3: Processing tables (preserving HTML structure)...", "active")
        
        try:
            from table_flattener import process_tables_in_markdown
            
            enhanced_md = doc_folder / f"{doc_name}_enhanced.md"
            final_md = doc_folder / f"{doc_name}_final.md"
            
            if enhanced_md.exists():
                process_tables_in_markdown(str(enhanced_md), str(final_md))
                update_status("✅ Table processing complete", "success")
            else:
                md_files = list(doc_folder.rglob("*.md"))
                original_md = max(md_files, key=lambda x: x.stat().st_size)
                shutil.copy(original_md, final_md)
                update_status("✅ Using original markdown", "success")
        except Exception as e:
            update_status(f"⚠️ Table processing warning: {str(e)[:100]}", "warning")
        
        # Step 5: Create chunks
        update_status("Step 4: Creating overlapping chunks...", "active")
        
        try:
            final_md = doc_folder / f"{doc_name}_final.md"
            chunks_path = doc_folder / f"{doc_name}_chunks_final.json"
            
            from overlap_chunker import OverlapChunker
            chunker = OverlapChunker(chunk_size=2000, overlap=300)
            chunks = chunker.chunk_markdown(str(final_md), str(chunks_path))
            update_status(f"✅ Created {len(chunks)} chunks", "success")
        except Exception as e:
            update_status(f"❌ Chunk creation failed: {str(e)}", "error")
            st.session_state.is_processing = False
            st.session_state.processing_started = False
            return
        
        # Step 6: Build vector store
        update_status("Step 5: Building vector store with embeddings...", "active")
        
        try:
            from vector_store import build_vector_store_from_chunks
            store_dir = doc_folder / "vector_store_final"
            build_vector_store_from_chunks(str(chunks_path), str(store_dir))
            update_status("✅ Vector store built successfully!", "success")
        except Exception as e:
            update_status(f"❌ Vector store build failed: {str(e)}", "error")
            st.session_state.is_processing = False
            st.session_state.processing_started = False
            return
        
        # Step 7: Load
        update_status("Step 6: Loading document into RAG system...", "active")
        
        vector_store = VectorStore()
        vector_store.load(str(store_dir))
        retriever = EnhancedRetriever(vector_store, str(chunks_path))
        
        st.session_state.retriever = retriever
        st.session_state.vector_store = vector_store
        st.session_state.current_doc_id = doc_name
        st.session_state.current_doc_name = file_name
        st.session_state.processing_complete = True
        st.session_state.last_uploaded_file_hash = file_hash
        st.session_state.messages = []
        
        try:
            from rag_llama import create_llama_rag
            st.session_state.rag = create_llama_rag(str(chunks_path), str(store_dir))
        except Exception as e:
            st.warning(f"RAG init warning: {e}")
            st.session_state.rag = None
        
        update_status("🎉 Document processing complete! Ready for Q&A.", "success")
        
    except Exception as e:
        update_status(f"❌ Processing error: {str(e)}", "error")
    finally:
        if Path(tmp_path).exists():
            os.unlink(tmp_path)
        st.session_state.is_processing = False
        st.session_state.processing_started = False
        st.session_state.pending_upload = None
        st.rerun()


def process_uploaded_document(uploaded_file):
    """Set up document processing."""
    if uploaded_file is None:
        return
    
    file_hash = hashlib.md5(uploaded_file.getvalue()).hexdigest()[:12]
    
    # Check if already processed
    if st.session_state.last_uploaded_file_hash == file_hash and st.session_state.processing_complete:
        st.info(f"📄 Document already loaded: {st.session_state.current_doc_name}")
        return
    
    # Check existing processed docs
    for doc_dir in Path("processed_docs").iterdir():
        if doc_dir.is_dir() and doc_dir.name.startswith(file_hash[:8]):
            st.info(f"📂 Loading previously processed document...")
            result = st.session_state.processor.load_document(doc_dir.name)
            if result["success"]:
                st.session_state.retriever = result["retriever"]
                st.session_state.vector_store = result["vector_store"]
                st.session_state.current_doc_id = doc_dir.name
                st.session_state.current_doc_name = uploaded_file.name
                st.session_state.processing_complete = True
                st.session_state.last_uploaded_file_hash = file_hash
                try:
                    from rag_llama import create_llama_rag
                    chunks_file = f"processed_docs/{doc_dir.name}/{doc_dir.name}_chunks_final.json"
                    store_dir = f"processed_docs/{doc_dir.name}/vector_store_final"
                    st.session_state.rag = create_llama_rag(chunks_file, store_dir)
                except:
                    st.session_state.rag = None
                st.rerun()
                return
    
    # Start new processing
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name
    
    st.session_state.is_processing = True
    st.session_state.processing_started = False
    st.session_state.status_messages = []
    st.session_state.pending_upload = {
        "tmp_path": tmp_path,
        "doc_name": uploaded_file.name.replace(".pdf", ""),
        "file_hash": file_hash,
        "file_name": uploaded_file.name
    }
    st.rerun()


def query_document(question: str, k: int = 5):
    """Query using local Llama models."""
    if not st.session_state.retriever:
        return None
    
    try:
        if st.session_state.rag:
            result = st.session_state.rag.query(question, k=k)
            return {
                "answer": result["answer"],
                "sources": result.get("sources", []),
                "used_vision": result.get("used_vision", False)
            }
        else:
            from rag_llama import LlamaRAG
            rag = LlamaRAG(
                retriever=st.session_state.retriever,
                text_model="llama3.2:3b",
                vision_model="qwen2.5vl:3b"
            )
            result = rag.query(question, k=k)
            return {
                "answer": result["answer"],
                "sources": result.get("sources", []),
                "used_vision": result.get("used_vision", False)
            }
    except Exception as e:
        return {"answer": f"Error: {str(e)}", "sources": [], "images": []}


# Sidebar
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h2 style="color: #ffffff;">📊</h2>
        <h3 style="color: #ffffff;">Document Intelligence</h3>
        <p style="color: #94a3b8; font-size: 0.8rem;">Multimodal RAG System</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 📄 Upload Document")
    
    uploaded_file = st.file_uploader(
        "Upload Annual Report (PDF)",
        type=["pdf"],
        key="doc_uploader",
        help="Upload a PDF document to analyze"
    )
    
    if uploaded_file and not st.session_state.is_processing:
        if st.button("🚀 Process Document", use_container_width=True):
            process_uploaded_document(uploaded_file)
    
    if st.session_state.processing_complete and st.session_state.current_doc_name:
        st.markdown(f"""
        <div style="background-color: #1e293b; padding: 0.5rem; border-radius: 8px; margin: 0.5rem 0;">
            <span style="color: #10b981;">✅ Active:</span>
            <span style="color: #e2e8f0; font-size: 0.8rem;">{st.session_state.current_doc_name[:30]}...</span>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    st.markdown("### ⚙️ Settings")
    k_value = st.slider("Retrieval Depth (k)", min_value=3, max_value=10, value=5)
    
    st.divider()
    
    if st.session_state.vector_store:
        stats = st.session_state.vector_store.get_stats()
        st.markdown("### 📊 Statistics")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Chunks", stats.get("total_chunks", 0))
        with col2:
            st.metric("Dimension", stats.get("dimension", 384))
    
    st.divider()
    
    if st.button("🔄 Reset Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    if st.button("🗑️ Clear Document", use_container_width=True):
        st.session_state.retriever = None
        st.session_state.vector_store = None
        st.session_state.current_doc_id = None
        st.session_state.current_doc_name = None
        st.session_state.processing_complete = False
        st.session_state.last_uploaded_file_hash = None
        st.session_state.messages = []
        st.session_state.rag = None
        st.session_state.status_messages = []
        st.rerun()
    
    st.markdown("""
    <div style="margin-top: 2rem;">
        <p style="color: #475569; font-size: 0.7rem; text-align: center;">
            Powered by Llama 3.2 + Qwen2.5VL<br>
            MinerU | FAISS | Streamlit
        </p>
    </div>
    """, unsafe_allow_html=True)


# Main content area
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown('<h1 style="text-align: center;">Document Intelligence</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #64748b;">Enterprise RAG for Annual Reports & Financial Documents</p>', unsafe_allow_html=True)

st.divider()

# Processing status
if st.session_state.is_processing:
    st.markdown("### 📋 Processing Document...")
    st.markdown("Please wait while the document is being processed. This may take 3-5 minutes.")
    
    if st.session_state.status_messages:
        for msg in st.session_state.status_messages[-10:]:
            icon = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌", "active": "⏳"}.get(msg["status"], "•")
            st.markdown(f"{icon} {msg['msg']}")
    else:
        st.markdown("⏳ Initializing...")
    
    if not st.session_state.processing_started and st.session_state.pending_upload:
        st.session_state.processing_started = True
        run_processing()
    
    st.stop()

# Display processing log if complete
if st.session_state.processing_complete and st.session_state.status_messages:
    with st.expander("📋 Processing Log", expanded=False):
        for msg in st.session_state.status_messages:
            icon = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌", "active": "⏳"}.get(msg["status"], "•")
            st.markdown(f"{icon} {msg['msg']}")

# Chat interface
if not st.session_state.processing_complete:
    st.info("👈 Upload a document and click 'Process Document' to begin.")
else:
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f"""
            <div class="user-message">
                <strong>You</strong><br>{message["content"]}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="assistant-message">
                <strong>Assistant</strong><br>{message["content"]}
            </div>
            """, unsafe_allow_html=True)
            
            if message.get("sources"):
                with st.expander("📚 View Sources"):
                    for source in message["sources"]:
                        st.markdown(f"""
                        <div class="source-card">
                            <div style="font-weight: 600; color: #4f46e5;">
                                Source {source.get('index', '?')} | {source.get('type', 'text').upper()} | Similarity: {source.get('similarity', 0):.3f}
                            </div>
                            <div style="font-family: monospace; font-size: 0.8rem;">
                                {source.get('content_preview', source.get('content', ''))[:300]}...
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
    
    st.divider()
    
    with st.container():
        col1, col2 = st.columns([5, 1])
        with col1:
            user_input = st.text_input(
                "Ask a question about the document",
                placeholder="e.g., What is the shareholding pattern?",
                key="user_input",
                label_visibility="collapsed"
            )
        with col2:
            send_button = st.button("Send", use_container_width=True)
    
    if send_button and user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.spinner("Analyzing document..."):
            result = query_document(user_input, k=k_value)
        if result:
            st.session_state.messages.append({
                "role": "assistant",
                "content": result["answer"],
                "sources": result.get("sources", [])
            })
        st.rerun()

# Footer
st.markdown("""
<div class="footer">
    <p>Confidential | Internal Use Only</p>
    <p>Multimodal RAG System © 2024 | All Rights Reserved</p>
</div>
""", unsafe_allow_html=True)