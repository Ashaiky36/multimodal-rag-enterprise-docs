# """
# Text extraction module for PDFs.
# Supports digital PDFs (pdfplumber) and scanned PDFs (OCR fallback).
# """

# import pdfplumber
# from pdf2image import convert_from_path
# import pytesseract
# from PIL import Image
# import logging
# from typing import Optional

# # Configure logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

# def extract_text_with_pdfplumber(pdf_path: str) -> Optional[str]:
#     """
#     Extract text from a digital PDF using pdfplumber.
#     Returns None if no text found.
#     """
#     try:
#         full_text = []
#         with pdfplumber.open(pdf_path) as pdf:
#             for page_num, page in enumerate(pdf.pages, start=1):
#                 text = page.extract_text()
#                 if text:
#                     full_text.append(f"--- Page {page_num} ---\n{text}\n")
#         result = "\n".join(full_text)
#         return result if result.strip() else None
#     except Exception as e:
#         logger.error(f"pdfplumber failed: {e}")
#         return None

# # def extract_text_with_ocr(pdf_path: str, dpi: int = 200) -> Optional[str]:
# #     """
# #     Fallback method: convert PDF pages to images and run Tesseract OCR.
# #     """
# #     try:
# #         images = convert_from_path(pdf_path, dpi=dpi)
# #         full_text = []
# #         for i, img in enumerate(images, start=1):
# #             # Use pytesseract to extract text
# #             text = pytesseract.image_to_string(img)
# #             if text.strip():
# #                 full_text.append(f"--- Page {i} (OCR) ---\n{text}\n")
# #             else:
# #                 full_text.append(f"--- Page {i} (OCR) ---\n[No text detected]\n")
# #         return "\n".join(full_text)
# #     except Exception as e:
# #         logger.error(f"OCR fallback failed: {e}")
# #         return None

# def extract_text_with_ocr(pdf_path, dpi=200):
#     try:
#         # Explicitly set poppler path (adjust to your installation)
#         poppler_path = r"C:\poppler\Library\bin"   # Change if you extracted elsewhere
        
#         # Use the poppler_path parameter
#         images = convert_from_path(pdf_path, dpi=dpi, poppler_path=poppler_path)
#         full_text = []
#         for i, img in enumerate(images, start=1):
#             text = pytesseract.image_to_string(img)
#             full_text.append(f"--- Page {i} (OCR) ---\n{text}\n")
#         return "\n".join(full_text)
#     except Exception as e:
#         logger.error(f"OCR failed: {e}")
#         return None

# def extract_text(pdf_path: str, prefer_ocr: bool = False) -> str:
#     """
#     Main extraction function: tries pdfplumber first, falls back to OCR.
#     If prefer_ocr=True, it uses OCR directly.
#     """
#     logger.info(f"Extracting text from: {pdf_path}")
    
#     if not prefer_ocr:
#         text = extract_text_with_pdfplumber(pdf_path)
#         if text and len(text.strip()) > 50:   # Heuristic: enough text
#             logger.info("Successfully extracted text using pdfplumber.")
#             return text
#         else:
#             logger.warning("pdfplumber returned little or no text. Falling back to OCR.")
#             text = extract_text_with_ocr(pdf_path)
#             if text:
#                 logger.info("OCR extraction successful.")
#                 return text
#             else:
#                 logger.error("Both extraction methods failed.")
#                 return ""
#     else:
#         logger.info("Using OCR as requested.")
#         text = extract_text_with_ocr(pdf_path)
#         return text if text else ""

# # Quick test if run directly
# if __name__ == "__main__":
#     import sys
#     if len(sys.argv) > 1:
#         pdf_file = sys.argv[1]
#         result = extract_text(pdf_file)
#         print("\n===== EXTRACTED TEXT =====\n")
#         print(result[:1000])  # preview first 1000 chars
#     else:
#         print("Usage: python text_extractor.py <path_to_pdf>")

import pdfplumber
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import logging

# ------------------- IMPORTANT: set Tesseract path -------------------
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# --------------------------------------------------------------------

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_text_with_pdfplumber(pdf_path):
    try:
        full_text = []
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if text:
                    full_text.append(f"--- Page {page_num} ---\n{text}\n")
        result = "\n".join(full_text)
        return result if result.strip() else None
    except Exception as e:
        logger.error(f"pdfplumber failed: {e}")
        return None

def extract_text_with_ocr(pdf_path, dpi=200):
    try:
        poppler_folder_path = r'C:\poppler\Library\bin' 
        
        images = convert_from_path(pdf_path, dpi=dpi, poppler_path=poppler_folder_path)
        full_text = []
        for i, img in enumerate(images, start=1):
            text = pytesseract.image_to_string(img)
            full_text.append(f"--- Page {i} (OCR) ---\n{text}\n")
        return "\n".join(full_text)
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        return None

def extract_text(pdf_path, prefer_ocr=False):
    logger.info(f"Extracting text from: {pdf_path}")
    if not prefer_ocr:
        text = extract_text_with_pdfplumber(pdf_path)
        if text and len(text.strip()) > 50:
            logger.info("Successfully extracted text using pdfplumber.")
            return text
        else:
            logger.warning("pdfplumber returned little or no text. Falling back to OCR.")
            text = extract_text_with_ocr(pdf_path)
            if text:
                logger.info("OCR extraction successful.")
                return text
            else:
                logger.error("Both extraction methods failed.")
                return ""
    else:
        logger.info("Using OCR as requested.")
        text = extract_text_with_ocr(pdf_path)
        return text if text else ""

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = extract_text(sys.argv[1])
        print("\n===== EXTRACTED TEXT =====\n")
        print(result[:1000])
    else:
        print("Usage: python text_extractor.py <path_to_pdf>")