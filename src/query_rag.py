# """
# Query the RAG system with HTML table support.
# """

# import sys
# from pathlib import Path
# import ollama
# import re

# sys.path.append("src")
# from vector_store import VectorStore
# from enhanced_retriever import EnhancedRetriever

# def ensure_vector_store(doc_name: str):
#     """Build vector store if it doesn't exist."""
#     import sys
#     sys.path.append('src')
    
#     chunks_file = f"processed_docs/{doc_name}/{doc_name}_chunks_final.json"
#     store_dir = f"processed_docs/{doc_name}/vector_store_final"
    
#     if not Path(store_dir).exists():
#         print(f"Vector store not found. Building from {chunks_file}...")
#         from vector_store import build_vector_store_from_chunks
#         build_vector_store_from_chunks(chunks_file, store_dir)
#         print("Vector store built successfully.")


# def extract_table_from_content(content: str) -> str:
#     """
#     Extract HTML table from content if present.
#     """
#     table_pattern = r'<table.*?</table>'
#     matches = re.findall(table_pattern, content, re.DOTALL | re.IGNORECASE)
#     if matches:
#         return matches[0]
#     return None


# def query_rag(question: str, doc_name: str, k: int = 5):
#     """
#     Query the RAG system with HTML table awareness.
#     """
#     chunks_file = f"processed_docs/{doc_name}/{doc_name}_chunks_final.json"
#     store_dir = f"processed_docs/{doc_name}/vector_store_final"
    
#     # Load vector store
#     vector_store = VectorStore()
#     vector_store.load(store_dir)
    
#     # Create retriever
#     retriever = EnhancedRetriever(vector_store, chunks_file)
    
#     # Retrieve chunks
#     results = retriever.search(question, k=k)
    
#     if not results:
#         print("No relevant information found.")
#         return
    
#     # Build context with table awareness
#     context_parts = []
#     for i, r in enumerate(results[:5]):
#         content = r.get("content", "")
        
#         # Check if this chunk contains a table
#         table = extract_table_from_content(content)
        
#         if table:
#             # If it's a table chunk, include the full HTML
#             context_parts.append(f"[Source {i+1} - TABLE]\n{table}")
#         else:
#             # Regular text chunk
#             context_parts.append(f"[Source {i+1} - TEXT]\n{content[:1500]}")
    
#     context = "\n\n".join(context_parts)
    
#     # Build prompt - instruct the model to read HTML tables properly
#     prompt = f"""You are a financial analyst. Answer the question based ONLY on the context below.

# IMPORTANT: The context may contain HTML tables (<table> tags). These tables contain structured financial data. Read them carefully by looking at the column headers and row labels to extract the correct numbers.

# CONTEXT:
# {context}

# QUESTION: {question}

# INSTRUCTIONS:
# - If the context contains HTML tables, parse them using the column headers
# - Pay attention to row labels (like "Standalone" vs "Consolidated", or "2022-23" vs "2021-22")
# - Extract the intersection of the correct row and column
# - If you cannot find the answer, say so

# ANSWER:"""
    
#     # Generate answer with Llama 3.2:3b
#     print("Generating answer with Llama 3.2:3b...")
#     response = ollama.generate(
#         model="llama3.2:3b",
#         prompt=prompt,
#         options={"temperature": 0.1, "num_predict": 500}
#     )
    
#     print(f"\nANSWER:\n{response['response']}\n")
    
#     # Show sources
#     print("SOURCES:")
#     for i, r in enumerate(results[:3]):
#         has_table = " (TABLE)" if "<table" in r.get("content", "") else ""
#         print(f"  {i+1}. Score: {r['similarity_score']:.3f}{has_table}")
#         preview = r.get("content", "").replace('\n', ' ')[:150]
#         print(f"     Preview: {preview}...")


# if __name__ == "__main__":
#     if len(sys.argv) < 3:
#         print("Usage: python query_rag.py <doc_name> <question>")
#         print("Example: python query_rag.py sample2 'What is the Standalone Net Profit for 2022-23?'")
#         sys.exit(1)
    
#     doc_name = sys.argv[1]
#     question = sys.argv[2]
    
#     query_rag(question, doc_name)

"""
Query the RAG system with improved model support.
"""

import sys
from pathlib import Path
import ollama
import re

sys.path.append("src")
from vector_store import VectorStore
from enhanced_retriever import EnhancedRetriever


def query_rag(question: str, doc_name: str, k: int = 5, model: str = "llama3.1:8b-instruct-q3_K_L"):
    """
    Query the RAG system with configurable model.
    
    Recommended models:
    - qwen2.5:3b (best balance, ~2.2GB)
    - phi3.5:3.8b-mini-instruct-q4_K_M (best reasoning)
    - llama3.1:8b-instruct-q3_K_L (best math, ~3.9GB)
    - mistral:7b-instruct-v0.3-q4_K_M (quality alternative)
    """
    chunks_file = f"processed_docs/{doc_name}/{doc_name}_chunks_final.json"
    store_dir = f"processed_docs/{doc_name}/vector_store_final"
    
    # Load vector store
    vector_store = VectorStore()
    vector_store.load(store_dir)
    
    # Create retriever
    retriever = EnhancedRetriever(vector_store, chunks_file)
    
    # Retrieve chunks
    results = retriever.search(question, k=k)
    
    if not results:
        print("No relevant information found.")
        return
    
    # Build context
    context_parts = []
    for i, r in enumerate(results[:5]):
        content = r.get("content", "")
        if "<table" in content:
            context_parts.append(f"[Source {i+1} - TABLE]\n{content}")
        else:
            context_parts.append(f"[Source {i+1} - TEXT]\n{content[:1500]}")
    
    context = "\n\n".join(context_parts)
    
    # Build prompt with better instructions
    prompt = f"""You are a financial auditor analyzing an annual report.

CONTEXT:
{context}

USER QUESTION:
{question}

INSTRUCTIONS:
1. READ the context carefully. The user may use different wording than the context.
2. If the context contains HTML tables, READ them as tables - the columns and rows are structured.
3. If calculations are needed (percentages, differences), SHOW your step-by-step math.
4. Extract numbers exactly as they appear in the context.
5. If you cannot find the answer, say "I cannot find this information."

ANSWER:"""
    
    print(f"Generating answer with {model}...")
    response = ollama.generate(
        model=model,
        prompt=prompt,
        options={"temperature": 0.1, "num_predict": 800}
    )
    
    print(f"\nANSWER:\n{response['response']}\n")
    
    # Show sources with similarity
    print("SOURCES:")
    for i, r in enumerate(results[:3]):
        has_table = " (TABLE)" if "<table" in r.get("content", "") else ""
        print(f"  {i+1}. Score: {r['similarity_score']:.3f}{has_table}")
        preview = r.get("content", "").replace('\n', ' ')[:150]
        print(f"     Preview: {preview}...")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python query_rag.py <doc_name> <question> [model]")
        print("Models: qwen2.5:3b (default), phi3.5, llama3.1:8b-q3, mistral")
        print("Example: python query_rag.py sample2 'What is the Standalone Net Profit?' qwen2.5:3b")
        sys.exit(1)
    
    doc_name = sys.argv[1]
    question = sys.argv[2]
    model = sys.argv[3] if len(sys.argv) > 3 else "llama3.1:8b-instruct-q3_K_L"
    
    query_rag(question, doc_name, model=model)