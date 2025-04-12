import qrcode
from io import BytesIO
import base64
from typing import Dict, Any

def generate_qr_code(data: Dict[str, Any]) -> str:
    """
    Generate a QR code from the given data
    :param data: Dictionary containing product information
    :return: Base64 encoded QR code image
    """
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(str(data))
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def validate_product_data(product_id, blockchain):
    """
    Validate product data against the blockchain
    :param product_id: ID of the product to validate
    :param blockchain: Blockchain instance
    :return: Boolean indicating if the product is valid
    """
    product_history = blockchain.get_product_history(product_id)
    return len(product_history) > 0 