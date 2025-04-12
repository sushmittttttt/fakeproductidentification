from typing import Dict, Any
from time import time
from blockchain import Blockchain
from utils import generate_qr_code, validate_product_data

class ProductManager:
    def __init__(self):
        self.blockchain = Blockchain()

    def register_product(self, product_id: str, manufacturer: str) -> Dict[str, Any]:
        """Register a new product on the blockchain."""
        product_data = {
            "product_id": product_id,
            "manufacturer": manufacturer,
            "timestamp": time()
        }

        if not validate_product_data(product_data):
            return {"success": False, "error": "Invalid product data"}

        # Add product to blockchain
        block = self.blockchain.add_block(product_data)
        
        # Generate QR code
        qr_code = generate_qr_code(product_data)

        return {
            "success": True,
            "block_index": block.index,
            "qr_code": qr_code,
            "product_data": product_data
        }

    def verify_product(self, product_id: str) -> Dict[str, Any]:
        """Verify if a product exists on the blockchain and check its validity."""
        result = self.blockchain.find_product(product_id)
        
        if not result["found"]:
            return {
                "verified": False,
                "message": "Product not found on blockchain",
                "is_fake": True
            }
        
        if not result["is_valid"]:
            return {
                "verified": False,
                "message": "Blockchain integrity compromised",
                "is_fake": True
            }
        
        return {
            "verified": True,
            "message": "Product verified successfully",
            "is_fake": False,
            "product_data": result["data"]
        } 