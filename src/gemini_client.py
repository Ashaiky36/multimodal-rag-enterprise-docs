"""
Gemini API client for text and vision capabilities.
Free tier: 15 requests per minute, 1 million tokens per day.
"""

import os
import base64
from pathlib import Path
from typing import Optional, Union, List, Dict
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class GeminiClient:
    """
    Google Gemini API client for RAG generation.
    Supports both text-only and multimodal (text + images) prompts.
    """
    
    # Available models as of June 2025
    AVAILABLE_MODELS = {
        "flash": "gemini-2.0-flash-exp",  # Fast, free tier
        "flash-lite": "gemini-2.0-flash-lite-preview-02-05",  # Lightweight
        "pro": "gemini-2.0-pro-exp-02-05",  # Most capable
        "flash-1.5": "gemini-1.5-flash",  # Older but stable
        "pro-1.5": "gemini-1.5-pro",  # Older pro version
    }
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-flash"):
        """
        Args:
            api_key: Google API key (or set GOOGLE_API_KEY environment variable)
            model: Model name or key from AVAILABLE_MODELS (default: "flash")
        """
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found. Get it from https://aistudio.google.com/")
        
        # Handle both short names and full model names
        if model in self.AVAILABLE_MODELS:
            self.model_name = self.AVAILABLE_MODELS[model]
        else:
            self.model_name = model
        
        self._init_client()
    
    def _init_client(self):
        """Initialize Gemini client with correct API version."""
        import google.generativeai as genai
        
        # Configure API
        genai.configure(api_key=self.api_key)
        
        # List available models for debugging
        try:
            models = genai.list_models()
            available = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
            logger.info(f"Available Gemini models: {available[:5]}...")
        except Exception as e:
            logger.warning(f"Cannot list models: {e}")
        
        # Initialize the model
        self.model = genai.GenerativeModel(self.model_name)
        logger.info(f"Gemini client initialized with model: {self.model_name}")
    
    def generate(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.2) -> str:
        """
        Generate response from text prompt.
        
        Args:
            prompt: Text prompt
            max_tokens: Maximum output tokens
            temperature: Lower = more deterministic (better for facts)
        """
        try:
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
                "top_p": 0.95
            }
            
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            # Try fallback model if available
            if "not found" in str(e):
                return self._try_fallback_model(prompt, max_tokens, temperature)
            return f"Error: {e}"
    
    def _try_fallback_model(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Try alternative model names if the primary fails."""
        import google.generativeai as genai
        
        fallback_models = ["gemini-1.5-flash", "gemini-pro", "gemini-1.0-pro"]
        
        for fallback in fallback_models:
            try:
                logger.info(f"Trying fallback model: {fallback}")
                model = genai.GenerativeModel(fallback)
                generation_config = {
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                }
                response = model.generate_content(prompt, generation_config=generation_config)
                logger.info(f"Success with fallback model: {fallback}")
                return response.text.strip()
            except Exception as e:
                logger.warning(f"Fallback {fallback} failed: {e}")
                continue
        
        return "Error: No working Gemini model found. Please check your API key and internet connection."
    
    def generate_with_image(self, prompt: str, image_path: str, max_tokens: int = 1000) -> str:
        """
        Generate response from text + image (for charts/graphs).
        """
        try:
            import google.generativeai as genai
            from PIL import Image
            
            img = Image.open(image_path)
            
            generation_config = {
                "temperature": 0.2,
                "max_output_tokens": max_tokens,
            }
            
            response = self.model.generate_content(
                [prompt, img],
                generation_config=generation_config
            )
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Gemini vision error: {e}")
            return f"Error: {e}"
    
    def generate_with_tables_and_chunks(self, question: str, context_chunks: List[Dict]) -> str:
        """
        Specialized method for RAG with retrieved chunks.
        """
        prompt = self._build_rag_prompt(question, context_chunks)
        
        image_chunks = [c for c in context_chunks if c.get("type") == "image" and c.get("image_path")]
        
        if image_chunks and image_chunks[0].get("image_path") and Path(image_chunks[0]["image_path"]).exists():
            return self.generate_with_image(prompt, image_chunks[0]["image_path"])
        else:
            return self.generate(prompt)
        
    def generate_with_image(self, prompt: str, image_path: str, max_tokens: int = 1000) -> str:
        """
        Generate response from text + image (for charts/graphs).
        
        Args:
            prompt: Text prompt about the image
            image_path: Path to image file (JPG, PNG)
            max_tokens: Maximum output tokens
        """
        try:
            import google.generativeai as genai
            from PIL import Image
            
            # Load and prepare image
            img = Image.open(image_path)
            
            generation_config = {
                "temperature": 0.2,
                "max_output_tokens": max_tokens,
            }
            
            # For Gemini 2.5 Flash, use the correct content format
            response = self.model.generate_content(
                [prompt, img],
                generation_config=generation_config
            )
            
            return response.text.strip()
        
        except Exception as e:
            logger.error(f"Gemini vision error: {e}")
            return f"Error: {e}"     
    
    def _build_rag_prompt(self, question: str, chunks: List[Dict]) -> str:
        """Build prompt from retrieved chunks."""
        context_parts = []
        
        for i, chunk in enumerate(chunks[:5]):
            chunk_type = chunk.get("type", "text")
            content = chunk.get("formatted_content", chunk.get("content", ""))
            page = chunk.get("page_num", "?")
            
            if chunk_type == "table":
                context_parts.append(f"\n[TABLE {i+1} - Page {page}]\n{content}")
            elif chunk_type == "image":
                context_parts.append(f"\n[IMAGE {i+1} - Page {page}]\nCaption: {chunk.get('content', 'No caption')}")
            else:
                context_parts.append(f"\n[TEXT {i+1} - Page {page}]\n{content}")
        
        context = "\n".join(context_parts)
        
        return f"""You are a financial analyst expert. Answer the question based ONLY on the provided context.

CONTEXT:
{context}

QUESTION: {question}

INSTRUCTIONS:
- Extract specific numbers from tables when available.
- If information is not in the context, say "I cannot find this in the document."
- Be precise and concise.
- Cite which source (TABLE/TEXT) you are using.

ANSWER:"""


# Alternative: Use requests directly if SDK has issues
class SimpleGeminiClient:
    """
    Fallback Gemini client using direct HTTP requests.
    Use if the SDK has version compatibility issues.
    """
    
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
    
    def generate(self, prompt: str, max_tokens: int = 1000) -> str:
        """Generate using REST API."""
        import requests
        
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": 0.2
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
            else:
                return f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Error: {e}"


if __name__ == "__main__":
    print("Testing Gemini connection...")
    
    # Try different model names
    for model_key in ["gemini-2.5-flash-preview", "gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.5-pro"]:
        print(f"\nTrying model: {model_key}")
        try:
            client = GeminiClient(model=model_key)
            response = client.generate("Say 'Hello' in 3 words.")
            print(f"Response: {response}")
            break
        except Exception as e:
            print(f"Failed: {e}")