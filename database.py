from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

# Initialize SQLAlchemy
db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)  # 'user' or 'manufacturer'
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    age = db.Column(db.Integer)
    sex = db.Column(db.String(10))
    address = db.Column(db.String(255))
    contact = db.Column(db.String(20))
    manufacturer_id = db.Column(db.Integer, db.ForeignKey('manufacturers.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.email}>'

class Manufacturer(db.Model):
    __tablename__ = 'manufacturers'
    
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), nullable=False)
    contact_person = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    contact = db.Column(db.String(20), nullable=False)
    registration_number = db.Column(db.String(50), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Manufacturer {self.company_name}>'

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    manufacturer_id = db.Column(db.Integer, db.ForeignKey('manufacturers.id'), nullable=False)
    product_id = db.Column(db.String(50), unique=True, nullable=False)
    product_type = db.Column(db.String(100), nullable=False)
    manufacturing_date = db.Column(db.DateTime, nullable=False)
    expiry_date = db.Column(db.DateTime, nullable=False)
    batch_number = db.Column(db.String(50), nullable=False)
    manufacturing_unit = db.Column(db.String(100), nullable=False)
    blockchain_hash = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Product {self.product_id}>'

class Verification(db.Model):
    __tablename__ = 'verifications'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    verification_code = db.Column(db.String(100))
    blockchain_transaction_id = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Verification {self.id}>'

class ProductImage(db.Model):
    __tablename__ = 'product_images'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ProductImage {self.id}>'

def add_product(manufacturer_id, product_data):
    """Add a new product to the database"""
    product = Product(
        manufacturer_id=manufacturer_id,
        product_id=product_data['product_id'],
        product_type=product_data['product_type'],
        manufacturing_date=datetime.strptime(product_data['manufacturing_date'], '%Y-%m-%d'),
        expiry_date=datetime.strptime(product_data['expiry_date'], '%Y-%m-%d'),
        batch_number=product_data['batch_number'],
        manufacturing_unit=product_data['manufacturing_unit']
    )
    
    db.session.add(product)
    db.session.commit()
    return product

def verify_product(product_id, user_id, status, verification_code, blockchain_tx_id):
    """Record a product verification"""
    verification = Verification(
        product_id=product_id,
        user_id=user_id,
        status=status,
        verification_code=verification_code,
        blockchain_transaction_id=blockchain_tx_id
    )
    
    db.session.add(verification)
    db.session.commit()
    return verification

def get_product(product_id):
    """Get a product by its ID"""
    return Product.query.filter_by(product_id=product_id).first()

def get_product_verifications(product_id):
    """Get all verifications for a product"""
    return Verification.query.filter_by(product_id=product_id).all()

def get_manufacturer_products(manufacturer_id):
    """Get all products for a manufacturer"""
    return Product.query.filter_by(manufacturer_id=manufacturer_id).all()

def add_product_image(product_id, image_url, is_primary=False):
    """Add an image to a product"""
    image = ProductImage(
        product_id=product_id,
        image_url=image_url,
        is_primary=is_primary
    )
    
    db.session.add(image)
    db.session.commit()
    return image

def get_product_images(product_id):
    """Get all images for a product"""
    return ProductImage.query.filter_by(product_id=product_id).all() 