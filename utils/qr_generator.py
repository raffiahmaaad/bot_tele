"""
QR Code generator utility.
"""

import io
import qrcode
from PIL import Image


def generate_qr_image(qris_string: str, size: int = 300) -> io.BytesIO:
    """
    Generate QR code image from QRIS string.
    
    Args:
        qris_string: QRIS payment string from Pakasir
        size: Size of the QR code in pixels
    
    Returns:
        BytesIO object containing PNG image
    """
    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qris_string)
    qr.make(fit=True)
    
    # Generate image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Resize if needed
    img = img.resize((size, size), Image.Resampling.LANCZOS)
    
    # Convert to bytes
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return buffer


def generate_qr_with_logo(qris_string: str, logo_path: str = None, size: int = 300) -> io.BytesIO:
    """
    Generate QR code with optional logo in center.
    
    Args:
        qris_string: QRIS payment string
        logo_path: Path to logo image (optional)
        size: Size of the QR code
    
    Returns:
        BytesIO object containing PNG image
    """
    # Create QR code with high error correction for logo
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(qris_string)
    qr.make(fit=True)
    
    # Generate image
    qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    qr_img = qr_img.resize((size, size), Image.Resampling.LANCZOS)
    
    # Add logo if provided
    if logo_path:
        try:
            logo = Image.open(logo_path)
            logo_size = size // 5  # Logo is 1/5 of QR size
            logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            
            # Calculate position to center logo
            pos = ((size - logo_size) // 2, (size - logo_size) // 2)
            qr_img.paste(logo, pos)
        except Exception as e:
            print(f"Warning: Could not add logo: {e}")
    
    # Convert to bytes
    buffer = io.BytesIO()
    qr_img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return buffer
