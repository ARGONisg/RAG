import fitz  # PyMuPDF
import re

def extract_text_from_pdf(file_path: str) -> list[dict]:
    """
    Extracts text from a PDF page by page. 
    Returns a list of dictionaries containing page numbers and text.
    """
    try:
        doc = fitz.open(file_path)
    except Exception as e:
        raise ValueError(f"Failed to open PDF {file_path}: {str(e)}")

    pages_data = []
    
    for i in range(len(doc)):
        page = doc[i]
        # Extract text, trying to preserve natural reading order
        text = page.get_text("text")
        
        # Clean up hyphenated line breaks (e.g., "informa-\ntion" -> "information")
        text = re.sub(r'-\n', '', text)
        
        # Replace multiple newlines and excessive whitespace with a single space
        text = re.sub(r'\s+', ' ', text).strip()
        
        if text:
            pages_data.append({
                "page_number": i + 1,
                "text": text
            })
            
    return pages_data