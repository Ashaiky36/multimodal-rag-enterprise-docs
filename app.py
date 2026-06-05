"""
Premium Corporate Document Intelligence System
Multimodal RAG for Enterprise Annual Reports
"""

import streamlit as st
import os
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import hashlib
import time

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

# Import modules
from vector_store import VectorStore
from enhanced_retriever import EnhancedRetriever
from gemini_client import GeminiClient
from image_linker import ImageLinker

# Page configuration - MUST be first Streamlit command
st.set_page_config(
    page_title="Document Intelligence | Corporate RAG",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for premium corporate design
st.markdown("""
<style>
    /* Main container */
    .main {
        background-color: #f8fafc;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #0f172a;
        padding: 2rem 1rem;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #e2e8f0;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #0f172a;
        font-weight: 600;
    }
    
    /* Chat messages */
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
    
    /* Source cards */
    .source-card {
        background-color: #f1f5f9;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
        border-left: 3px solid #6366f1;
        font-size: 0.85rem;
    }
    
    .source-header {
        font-weight: 600;
        color: #4f46e5;
        margin-bottom: 8px;
    }
    
    /* Upload section */
    .upload-container {
        border: 2px dashed #cbd5e1;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        background-color: #f8fafc;
    }
    
    /* Metrics */
    .metric-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #0f172a;
    }
    
    .metric-label {
        font-size: 0.8rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Status badges */
    .badge-success {
        background-color: #dcfce7;
        color: #166534;
        padding: 4px 8px;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 500;
    }
    
    .badge-warning {
        background-color: #fef9c3;
        color: #854d0e;
        padding: 4px 8px;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 500;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 1.5rem;
        color: #94a3b8;
        font-size: 0.75rem;
        border-top: 1px solid #e2e8f0;
        margin-top: 2rem;
    }
    
    /* Custom button */
    .stButton button {
        background-color: #4f46e5;
        color: white;
        border-radius: 8px;
        font-weight: 500;
    }
    
    .stButton button:hover {
        background-color: #6366f1;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "retriever" not in st.session_state:
    st.session_state.retriever = None
if "current_document" not in st.session_state:
    st.session_state.current_document = None
if "processing_complete" not in st.session_state:
    st.session_state.processing_complete = False
if "rag_chain" not in st.session_state:
    st.session_state.rag_chain = None
if "image_linker" not in st.session_state:
    st.session_state.image_linker = None


# def process_uploaded_document(uploaded_file):
#     """
#     Process uploaded document and initialize vector store.
#     """
#     try:
#         # Save uploaded file temporarily
#         with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
#             tmp_file.write(uploaded_file.getvalue())
#             tmp_path = tmp_file.name
        
#         st.info(f"Processing: {uploaded_file.name}")
        
#         # TODO: Integrate MinerU processing here
#         # For now, use existing processed document or show placeholder
        
#         # For demo, check if we have pre-processed document
#         chunks_path = Path("outputs/sample_digital1_chunks.json")
#         store_path = "vector_store"
        
#         if chunks_path.exists():
#             # Load existing vector store
#             vector_store = VectorStore()
#             vector_store.load(store_path)
#             retriever = EnhancedRetriever(vector_store, str(chunks_path))
            
#             # Load image linker
#             md_path = Path("outputs/sample_digital1/auto/sample_digital1.md")
#             images_path = "outputs/sample_digital1/auto/images"
            
#             if md_path.exists() and Path(images_path).exists():
#                 image_linker = ImageLinker(str(md_path), images_path)
#                 st.session_state.image_linker = image_linker
            
#             st.session_state.vector_store = vector_store
#             st.session_state.retriever = retriever
#             st.session_state.current_document = uploaded_file.name
#             st.session_state.processing_complete = True
            
#             # Clean up temp file
#             os.unlink(tmp_path)
            
#             return True
#         else:
#             st.error("No pre-processed document found. Please ensure MinerU has been run on your document.")
#             return False
            
#     except Exception as e:
#         st.error(f"Error processing document: {str(e)}")
#         return False
def process_uploaded_document(uploaded_file):
    """
    Process uploaded document and initialize vector store.
    """
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        st.info(f"Processing: {uploaded_file.name}")
        
        # USE OVERLAPPING CHUNKS - UPDATE THESE PATHS
        chunks_file = "outputs/sample_digital1_chunks_overlap.json"
        store_dir = "vector_store_overlap"
        
        # Check if chunks file exists
        chunks_path = Path(chunks_file)
        store_path = Path(store_dir)
        
        if chunks_path.exists() and store_path.exists():
            # Load existing vector store with overlapping chunks
            from vector_store import VectorStore
            from enhanced_retriever import EnhancedRetriever
            from image_linker import ImageLinker
            
            vector_store = VectorStore()
            vector_store.load(str(store_path))
            retriever = EnhancedRetriever(vector_store, str(chunks_path))
            
            # Load image linker
            md_path = Path("outputs/sample_digital1/auto/sample_digital1.md")
            images_path = "outputs/sample_digital1/auto/images"
            
            if not md_path.exists():
                md_path = Path("outputs/sample_digital1/auto/content.md")
            
            if md_path.exists() and Path(images_path).exists():
                image_linker = ImageLinker(str(md_path), images_path)
                st.session_state.image_linker = image_linker
            
            st.session_state.vector_store = vector_store
            st.session_state.retriever = retriever
            st.session_state.current_document = uploaded_file.name
            st.session_state.processing_complete = True
            
            # Clean up temp file
            os.unlink(tmp_path)
            
            return True
        else:
            st.error(f"Pre-processed document not found. Please ensure:\n- {chunks_file} exists\n- {store_dir} exists")
            return False
            
    except Exception as e:
        st.error(f"Error processing document: {str(e)}")
        return False

def query_document(question: str, k: int = 5):
    """
    Query the document and return answer with sources.
    """
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
                "content": result.get("content", "")[:500],
                "full_content": result.get("content", "")
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
    # Logo / Brand
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h2 style="color: #ffffff;">📊</h2>
        <h3 style="color: #ffffff;">Document Intelligence</h3>
        <p style="color: #94a3b8; font-size: 0.8rem;">Multimodal RAG System</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Document Upload Section
    st.markdown("### 📄 Document")
    
    uploaded_file = st.file_uploader(
        "Upload Annual Report (PDF)",
        type=["pdf"],
        help="Upload a PDF document to analyze"
    )
    
    if uploaded_file and st.session_state.current_document != uploaded_file.name:
        with st.spinner("Processing document..."):
            if process_uploaded_document(uploaded_file):
                st.success(f"✅ Ready: {uploaded_file.name}")
                st.session_state.messages = []  # Clear chat history
            else:
                st.error("Processing failed")
    
    if st.session_state.current_document:
        st.markdown(f"""
        <div class="badge-success" style="display: inline-block;">
            Active: {st.session_state.current_document[:30]}...
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Settings
    st.markdown("### ⚙️ Settings")
    k_value = st.slider("Retrieval Depth (k)", min_value=3, max_value=10, value=5, help="Number of chunks to retrieve")
    
    st.divider()
    
    # Stats
    # if st.session_state.retriever and st.session_state.vector_store:
    #     stats = st.session_state.vector_store.get_stats()
    #     st.markdown("### 📊 Statistics")
    #     col1, col2 = st.columns(2)
    #     with col1:
    #         st.metric("Chunks", stats.get("total_chunks", 0))
    #     with col2:
    #         st.metric("Dimension", stats.get("dimension", 384))
    
    # st.divider()
    # Stats
    if st.session_state.retriever and st.session_state.vector_store:
        stats = st.session_state.vector_store.get_stats()
        st.markdown("### 📊 Statistics")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Chunks", stats.get("total_chunks", 0))
        with col2:
            st.metric("Dimension", stats.get("dimension", 384))
        
        # Show which chunks file is being used
        if st.session_state.get("chunks_file"):
            st.caption(f"📁 {Path(st.session_state.chunks_file).name}")
        
    # Reset button
    if st.button("🔄 Reset Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    # Footer
    st.markdown("""
    <div style="position: fixed; bottom: 1rem; left: 1rem; right: 1rem;">
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

# Status indicator
if not st.session_state.processing_complete:
    st.info("👈 Please upload a document from the sidebar to begin.")
else:
    # Chat interface
    chat_container = st.container()
    
    with chat_container:
        # Display chat history
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.markdown(f"""
                <div class="user-message">
                    <strong>You</strong><br>{message["content"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                # Assistant message with possible sources
                st.markdown(f"""
                <div class="assistant-message">
                    <strong>Assistant</strong><br>{message["content"]}
                </div>
                """, unsafe_allow_html=True)
                
                # Display sources if available
                if message.get("sources"):
                    with st.expander("📚 View Sources"):
                        for source in message["sources"]:
                            st.markdown(f"""
                            <div class="source-card">
                                <div class="source-header">
                                    Source {source['index']} | {source['type'].upper()} | Similarity: {source['similarity']:.3f}
                                </div>
                                <div style="font-family: monospace; font-size: 0.8rem;">
                                    {source['content']}...
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                
                # Display images if used
                if message.get("images"):
                    st.caption(f"📷 Analyzed {len(message['images'])} chart(s)")
    
    # Input area
    st.divider()
    
    with st.container():
        col1, col2 = st.columns([5, 1])
        with col1:
            user_input = st.text_input(
                "Ask a question about the document",
                placeholder="e.g., What is the shareholding pattern? or Describe the revenue trend...",
                key="user_input",
                label_visibility="collapsed"
            )
        with col2:
            send_button = st.button("Send", use_container_width=True)
    
    if send_button and user_input:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Generate response
        with st.spinner("Analyzing document..."):
            result = query_document(user_input, k=k_value)
        
        if result:
            # Add assistant message with sources
            assistant_message = {
                "role": "assistant",
                "content": result["answer"],
                "sources": result.get("sources", []),
                "images": result.get("images", [])
            }
            st.session_state.messages.append(assistant_message)
        
        st.rerun()

# Footer
st.markdown("""
<div class="footer">
    <p>Confidential | Internal Use Only</p>
    <p>Multimodal RAG System © 2024 | All Rights Reserved</p>
</div>
""", unsafe_allow_html=True)