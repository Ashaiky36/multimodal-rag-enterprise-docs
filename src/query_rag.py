

# """
# Query the RAG system with improved model support.
# """

# import sys
# from pathlib import Path
# import ollama
# import re

# sys.path.append("src")
# from vector_store import VectorStore
# from enhanced_retriever import EnhancedRetriever


# def query_rag(question: str, doc_name: str, k: int = 5, model: str = "llama3.1:8b-instruct-q3_K_L"):
#     """
#     Query the RAG system with configurable model.
    
#     Recommended models:
#     - qwen2.5:3b (best balance, ~2.2GB)
#     - phi3.5:3.8b-mini-instruct-q4_K_M (best reasoning)
#     - llama3.1:8b-instruct-q3_K_L (best math, ~3.9GB)
#     - mistral:7b-instruct-v0.3-q4_K_M (quality alternative)
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
    
#     # Build context
#     context_parts = []
#     for i, r in enumerate(results[:5]):
#         content = r.get("content", "")
#         if "<table" in content:
#             context_parts.append(f"[Source {i+1} - TABLE]\n{content}")
#         else:
#             context_parts.append(f"[Source {i+1} - TEXT]\n{content[:1500]}")
    
#     context = "\n\n".join(context_parts)
    
#     # Build prompt with better instructions
#     prompt = f"""You are a financial auditor analyzing an annual report.

# CONTEXT:
# {context}

# USER QUESTION:
# {question}

# INSTRUCTIONS:
# 1. READ the context carefully. The user may use different wording than the context.
# 2. If the context contains HTML tables, READ them as tables - the columns and rows are structured.
# 3. If calculations are needed (percentages, differences), SHOW your step-by-step math.
# 4. Extract numbers exactly as they appear in the context.
# 5. If you cannot find the answer, say "I cannot find this information."

# ANSWER:"""
    
#     print(f"Generating answer with {model}...")
#     response = ollama.generate(
#         model=model,
#         prompt=prompt,
#         options={"temperature": 0.1, "num_predict": 800}
#     )
    
#     print(f"\nANSWER:\n{response['response']}\n")
    
#     # Show sources with similarity
#     print("SOURCES:")
#     for i, r in enumerate(results[:3]):
#         has_table = " (TABLE)" if "<table" in r.get("content", "") else ""
#         print(f"  {i+1}. Score: {r['similarity_score']:.3f}{has_table}")
#         preview = r.get("content", "").replace('\n', ' ')[:150]
#         print(f"     Preview: {preview}...")


# if __name__ == "__main__":
#     if len(sys.argv) < 3:
#         print("Usage: python query_rag.py <doc_name> <question> [model]")
#         print("Models: qwen2.5:3b (default), phi3.5, llama3.1:8b-q3, mistral")
#         print("Example: python query_rag.py sample2 'What is the Standalone Net Profit?' qwen2.5:3b")
#         sys.exit(1)
    
#     doc_name = sys.argv[1]
#     question = sys.argv[2]
#     model = sys.argv[3] if len(sys.argv) > 3 else "llama3.1:8b-instruct-q3_K_L"
    
#     query_rag(question, doc_name, model=model)

"""
Query the RAG system with optimized token settings.
"""

import sys
from pathlib import Path
import ollama
import re

sys.path.append("src")
from vector_store import VectorStore
from enhanced_retriever import EnhancedRetriever


def query_rag(question: str, doc_name: str, k: int = 5, model: str = "gemma3:4b-it-qat"):
    """
    Query the RAG system with optimized token settings.
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
            context_parts.append(f"[Source {i+1} - TABLE]\n{content[:2000]}")
        else:
            context_parts.append(f"[Source {i+1} - TEXT]\n{content[:1500]}")
    
    context = "\n\n".join(context_parts)
    
    # Build prompt with token efficiency
    prompt = f"""You are a precise financial analyst. Answer directly using ONLY the context.

CONTEXT:
{context}

QUESTION: {question}

CRITICAL INSTRUCTIONS - FOLLOW EXACTLY:
1. DO NOT quote, copy, or reproduce ANY part of the context in your answer.
2. DO NOT say "According to the context" or "Based on the table above".
3. DO NOT reproduce tables, HTML, or large blocks of text.
4. READ the context silently, then write your answer in your own words.
5. If citing data, state values directly without referencing the source.
6. Show math concisely (e.g., "7283 - 7226 = 57").
7. If you cannot find the answer, say "I cannot find this information."

ANSWER (your own words, no quotes):"""
    
#     prompt = f"""You are a precise financial analyst. Answer directly using ONLY the context.

# CONTEXT:
# {context}

# QUESTION: {question}

# INSTRUCTIONS:
# 1. Start answering immediately. No filler.
# 2. If citing data, state values directly.
# 3. Show math concisely (e.g., "7283 - 7226 = 57").
# 4. If you cannot find the answer, say so.

# ANSWER:"""
    
    print(f"Generating answer with {model}...")
    print(f"Model config: num_predict=4096, num_ctx=8192")
    
    response = ollama.generate(
        model=model,
        prompt=prompt,
        options={
             "temperature": 0.1,
             "num_predict": 4096,              # Longer responses
             "num_ctx": 8192,                  # Large context
             "num_batch": 512,
             "num_gpu": 40,                    # Use more GPU layers
             "main_gpu": 0,
             "tensor_split": "4,4",            # Balanced split
             "top_k": 40,
             "top_p": 0.9,
             "repeat_penalty": 1.1
            #   "temperature": 0.1,
            #   "num_predict": 2048,           # REDUCED from 4096 (still gives ~1500 words)
            #   "num_ctx": 4096,               # REDUCED from 8192 (still fits medium tables)
            #   "num_batch": 512,              # ADDED: Processes tokens in smaller batches
            #   "num_gpu": 35,                 # ADDED: Offloads 35 layers to GPU
            #   "main_gpu": 0,                 # ADDED: Uses GPU 0 for main computation
            #   "tensor_split": "4,4",          # Splits compute between VRAM and system RAM
            #   "top_k": 40,
            #   "top_p": 0.9,
            #   "repeat_penalty": 1.1
            # "temperature": 0.1,
            # "num_predict": 4096,   # MAX RESPONSE TOKENS
            # "num_ctx": 8192,       # CONTEXT WINDOW
            # "top_k": 40,
            # "top_p": 0.9,
            # "repeat_penalty": 1.1
        }
    )
    
    answer = response['response'].strip()
    
    print(f"\nANSWER:\n{answer}")
    print(f"\nResponse length: {len(answer)} characters, {len(answer.split())} words")
    
    # Show sources
    print("\nSOURCES:")
    for i, r in enumerate(results[:3]):
        has_table = " (TABLE)" if "<table" in r.get("content", "") else ""
        print(f"  {i+1}. Score: {r['similarity_score']:.3f}{has_table}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python query_rag.py <doc_name> <question> [model]")
        print("Default model: llama3.1:8b-instruct-q3_K_L")
        print("Example: python query_rag.py sample2 'What is the shareholding pattern?'")
        sys.exit(1)
    
    doc_name = sys.argv[1]
    question = sys.argv[2]
    model = sys.argv[3] if len(sys.argv) > 3 else "llama3.1:8b-instruct-q3_K_L"
    
    query_rag(question, doc_name, model=model)