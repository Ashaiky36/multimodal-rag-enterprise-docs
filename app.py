"""
Premium Corporate Document Intelligence System
Multimodal RAG for Enterprise Annual Reports
"""

import streamlit as st
import os
import sys
import tempfile
import shutil
import atexit
from pathlib import Path
from datetime import datetime
import hashlib

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

# Import modules
from vector_store import VectorStore
from enhanced_retriever import EnhancedRetriever
from gemini_client import GeminiClient
from image_linker import ImageLinker
from document_processor import DocumentProcessor

# Page configuration
st.set_page_config(
    page_title="Document Intelligence | Corporate RAG",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for premium corporate design
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


# Call initialization
init_session_state()


def process_uploaded_document(uploaded_file):
    """
    Process a single uploaded document.
    Only processes if it's a new document.
    """
    if uploaded_file is None:
        return False
    
    # Calculate file hash
    file_hash = hashlib.md5(uploaded_file.getvalue()).hexdigest()[:12]
    
    # Check if this exact file was already processed
    if st.session_state.last_uploaded_file_hash == file_hash and st.session_state.processing_complete:
        st.info(f"Document already loaded: {st.session_state.current_doc_name}")
        return True
    
    # Check if already processed in processed_docs folder
    for doc_dir in Path("processed_docs").iterdir():
        if doc_dir.is_dir() and doc_dir.name.startswith(file_hash[:8]):
            st.info(f"Loading previously processed document...")
            result = st.session_state.processor.load_document(doc_dir.name)
            if result["success"]:
                st.session_state.retriever = result["retriever"]
                st.session_state.vector_store = result["vector_store"]
                st.session_state.image_linker = result["image_linker"]
                st.session_state.current_doc_id = doc_dir.name
                st.session_state.current_doc_name = uploaded_file.name
                st.session_state.processing_complete = True
                st.session_state.last_uploaded_file_hash = file_hash
                return True
    
    # Set processing flag to prevent duplicate processing
    st.session_state.is_processing = True
    
    # Process new document
    with st.spinner(f"Processing {uploaded_file.name}... (this may take 3-5 minutes)"):
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        try:
            # Process document
            result = st.session_state.processor.process_document(
                tmp_path, 
                uploaded_file.name.replace(".pdf", "")
            )
            
            if result["success"]:
                # Load the processed document components
                doc_id = result["doc_id"]
                load_result = st.session_state.processor.load_document(doc_id)
                
                if load_result["success"]:
                    st.session_state.retriever = load_result["retriever"]
                    st.session_state.vector_store = load_result["vector_store"]
                    st.session_state.image_linker = load_result["image_linker"]
                    st.session_state.current_doc_id = doc_id
                    st.session_state.current_doc_name = uploaded_file.name
                    st.session_state.processing_complete = True
                    st.session_state.last_uploaded_file_hash = file_hash
                    st.session_state.messages = []
                    st.success(f"✅ Document ready: {uploaded_file.name}")
                    return True
            else:
                st.error(f"Processing failed: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            st.error(f"Error: {e}")
            return False
        finally:
            # Clean up temp file
            if Path(tmp_path).exists():
                os.unlink(tmp_path)
            st.session_state.is_processing = False
    
    return False


def query_document(question: str, k: int = 5):
    """Query the document and return answer with sources."""
    if not st.session_state.retriever:
        return None
    
    try:
        # Retrieve chunks
        results = st.session_state.retriever.search(question, k=k)
        
        if not results:
            return {
                "answer": "No relevant information found in the document.",
                "sources": [],
                "images": []
            }
        
        # Check if visual question
        visual_keywords = ["chart", "graph", "plot", "figure", "trajectory", "intersect", "line", "trend"]
        is_visual = any(kw in question.lower() for kw in visual_keywords)
        
        # Find images if visual
        attached_images = []
        if is_visual and st.session_state.image_linker:
            attached_images = st.session_state.image_linker.find_images_for_query(question)
        
        # Build context
        context = "\n\n".join([
            f"Source {i+1}:\n{r.get('content', '')[:800]}"
            for i, r in enumerate(results[:5])
        ])
        
        # Generate answer
        gemini = GeminiClient()
        
        if attached_images:
            prompt = f"""Analyze the attached chart(s) from the annual report.

QUESTION: {question}

INSTRUCTIONS:
- Look at the visual elements: lines, axes, labels
- Describe trajectory, trends, and intersections
- Answer based on what you SEE in the chart

ANSWER:"""
            answer = gemini.generate_with_image(prompt, attached_images[0])
        else:
            prompt = f"""Answer based ONLY on the context below.

CONTEXT:
{context}

QUESTION: {question}

INSTRUCTIONS:
- Extract exact numbers from tables
- Be precise and concise
- Cite the source when possible

ANSWER:"""
            answer = gemini.generate(prompt)
        
        # Prepare sources
        sources = []
        for i, result in enumerate(results[:3]):
            sources.append({
                "index": i + 1,
                "type": result.get("type", "text"),
                "similarity": result.get("similarity_score", 0),
                "content": result.get("content", "")[:500]
            })
        
        return {
            "answer": answer,
            "sources": sources,
            "images": attached_images,
            "used_vision": len(attached_images) > 0
        }
        
    except Exception as e:
        return {
            "answer": f"Error generating response: {str(e)}",
            "sources": [],
            "images": []
        }


# Sidebar
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h2 style="color: #ffffff;">📊</h2>
        <h3 style="color: #ffffff;">Document Intelligence</h3>
        <p style="color: #94a3b8; font-size: 0.8rem;">Multimodal RAG System</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Document Upload Section
    st.markdown("### 📄 Upload Document")
    
    uploaded_file = st.file_uploader(
        "Upload Annual Report (PDF)",
        type=["pdf"],
        key="doc_uploader",
        help="Upload a PDF document to analyze"
    )
    
    if uploaded_file and not st.session_state.is_processing:
        # Check if this is a new file (different from last uploaded)
        current_hash = hashlib.md5(uploaded_file.getvalue()).hexdigest()[:12]
        if current_hash != st.session_state.last_uploaded_file_hash:
            process_uploaded_document(uploaded_file)
            st.rerun()
    
    if st.session_state.processing_complete and st.session_state.current_doc_name:
        st.markdown(f"""
        <div style="background-color: #1e293b; padding: 0.5rem; border-radius: 8px; margin: 0.5rem 0;">
            <span style="color: #10b981;">✅ Active:</span>
            <span style="color: #e2e8f0; font-size: 0.8rem;">{st.session_state.current_doc_name[:30]}...</span>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Settings
    st.markdown("### ⚙️ Settings")
    k_value = st.slider("Retrieval Depth (k)", min_value=3, max_value=10, value=5)
    
    st.divider()
    
    # Stats
    if st.session_state.vector_store:
        stats = st.session_state.vector_store.get_stats()
        st.markdown("### 📊 Statistics")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Chunks", stats.get("total_chunks", 0))
        with col2:
            st.metric("Dimension", stats.get("dimension", 384))
    
    st.divider()
    
    # Reset conversation
    if st.button("🔄 Reset Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    # Clear session (delete current document from memory, not disk)
    if st.button("🗑️ Clear Document", use_container_width=True):
        st.session_state.retriever = None
        st.session_state.vector_store = None
        st.session_state.image_linker = None
        st.session_state.current_doc_id = None
        st.session_state.current_doc_name = None
        st.session_state.processing_complete = False
        st.session_state.last_uploaded_file_hash = None
        st.session_state.messages = []
        st.rerun()
    
    # Footer
    st.markdown("""
    <div style="margin-top: 2rem;">
        <p style="color: #475569; font-size: 0.7rem; text-align: center;">
            Powered by Gemini 2.5 Flash<br>
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

# Chat interface
if not st.session_state.processing_complete:
    st.info("👈 Please upload a document from the sidebar to begin.")
else:
    # Display chat history
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
                                Source {source['index']} | {source['type'].upper()} | Similarity: {source['similarity']:.3f}
                            </div>
                            <div style="font-family: monospace; font-size: 0.8rem;">
                                {source['content']}...
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
    
    # Input area
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