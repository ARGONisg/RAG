import re

def chunk_text(pages: list[dict], max_chars: int = 512, overlap: int = 64) -> list[dict]:
    """
    Recursively chunks text into semantic windows with defined overlap.
    Retains page metadata for citations.
    """
    chunks = []
    
    for page in pages:
        text = page["text"]
        page_num = page["page_number"]
        
        # Split by semantic boundaries (sentences)
        sentences = re.split(r'(?<=[.?!])\s+', text)
        
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= max_chars:
                current_chunk += sentence + " "
            else:
                if current_chunk.strip():
                    chunks.append({"text": current_chunk.strip(), "page_number": page_num})
                
                # Apply overlap by taking the last 'overlap' characters of the previous chunk
                # and finding the nearest word boundary to start the new chunk cleanly
                if len(current_chunk) > overlap:
                    overlap_text = current_chunk[-overlap:]
                    # Snip at the first space to avoid partial words
                    overlap_text = overlap_text[overlap_text.find(" ")+1:] 
                else:
                    overlap_text = current_chunk
                    
                current_chunk = overlap_text + sentence + " "
                
        if current_chunk.strip():
            chunks.append({"text": current_chunk.strip(), "page_number": page_num})
            
    return chunks