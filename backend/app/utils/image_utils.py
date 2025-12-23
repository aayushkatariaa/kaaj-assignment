"""
Image utilities for converting PDFs to images
"""

import os
import fitz  # PyMuPDF
from pathlib import Path
from PIL import Image
import io
from typing import List


def pdf_to_images(pdf_path: str, output_dir: str = None, dpi: int = 300) -> List[str]:
    """
    Convert a PDF file to images (one image per page).
    
    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save images (defaults to temp directory)
        dpi: Resolution for rendering (default: 300)
    
    Returns:
        List of paths to the generated images
    """
    if output_dir is None:
        output_dir = Path(pdf_path).parent / "temp_images"
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Get base filename without extension
    pdf_name = Path(pdf_path).stem
    
    # Open PDF
    doc = fitz.open(pdf_path)
    
    image_paths = []
    
    # Calculate zoom factor for DPI
    zoom = dpi / 72  # 72 is the default DPI in PDFs
    mat = fitz.Matrix(zoom, zoom)
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Render page to pixmap
        pix = page.get_pixmap(matrix=mat)
        
        # Save as PNG
        image_path = os.path.join(output_dir, f"{pdf_name}_page_{page_num + 1}.png")
        pix.save(image_path)
        
        image_paths.append(image_path)
    
    doc.close()
    
    return image_paths


def pdf_to_images_base64(pdf_path: str, dpi: int = 300) -> List[str]:
    """
    Convert a PDF file to base64-encoded images.
    
    Args:
        pdf_path: Path to the PDF file
        dpi: Resolution for rendering (default: 300)
    
    Returns:
        List of base64-encoded PNG images
    """
    import base64
    
    # Open PDF
    doc = fitz.open(pdf_path)
    
    base64_images = []
    
    # Calculate zoom factor for DPI
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Render page to pixmap
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to PNG bytes
        png_bytes = pix.tobytes("png")
        
        # Encode to base64
        base64_image = base64.b64encode(png_bytes).decode('utf-8')
        base64_images.append(base64_image)
    
    doc.close()
    
    return base64_images


def cleanup_temp_images(image_paths: List[str]) -> None:
    """
    Clean up temporary image files.
    
    Args:
        image_paths: List of image file paths to delete
    """
    for image_path in image_paths:
        try:
            if os.path.exists(image_path):
                os.remove(image_path)
        except Exception as e:
            print(f"Warning: Could not delete {image_path}: {e}")
    
    # Try to remove the temp directory if empty
    if image_paths:
        temp_dir = Path(image_paths[0]).parent
        try:
            if temp_dir.exists() and not list(temp_dir.iterdir()):
                temp_dir.rmdir()
        except Exception:
            pass  # Ignore errors when removing directory
