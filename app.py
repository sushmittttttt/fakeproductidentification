from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, send_file
from blockchain import Blockchain
from utils import generate_qr_code, validate_product_data
from database import db, User, Manufacturer, Product, Verification, ProductImage
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_cors import CORS
import os
import qrcode
from io import BytesIO
import base64
import json

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database
db.init_app(app)

# Create database tables
with app.app_context():
    db.create_all()

# Initialize blockchain
blockchain = Blockchain()

@app.template_filter('datetime')
def format_datetime(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        user_type = request.form.get('user_type')
        if user_type == 'user':
            return redirect(url_for('user_signup'))
        else:
            return redirect(url_for('manufacturer_signup'))
    return render_template('signup.html')

@app.route('/user/signup', methods=['GET', 'POST'])
def user_signup():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        age = request.form.get('age')
        sex = request.form.get('sex')
        address = request.form.get('address')
        contact = request.form.get('contact')

        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('user_signup'))

        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=generate_password_hash(password),
            age=age,
            sex=sex,
            address=address,
            contact=contact
        )
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))

    return render_template('user_signup.html')

@app.route('/manufacturer_signup', methods=['GET', 'POST'])
def manufacturer_signup():
    if request.method == 'POST':
        company_name = request.form.get('company_name')
        email = request.form.get('email')
        password = request.form.get('password')
        contact_person = request.form.get('contact_person')
        address = request.form.get('address')
        contact = request.form.get('contact')
        registration_number = request.form.get('registration_number')

        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered!', 'error')
            return redirect(url_for('manufacturer_signup'))

        # Create new manufacturer
        manufacturer = Manufacturer(
            company_name=company_name,
            contact_person=contact_person,
            address=address,
            contact=contact,
            registration_number=registration_number
        )
        db.session.add(manufacturer)
        db.session.commit()

        # Create user account
        user = User(
            email=email,
            password=generate_password_hash(password),
            user_type='manufacturer',
            manufacturer_id=manufacturer.id
        )
        db.session.add(user)
        db.session.commit()

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('manufacturer_signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user_type = request.form.get('user_type')

        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password) and user.user_type == user_type:
            # Clear any existing session
            session.clear()
            
            # Set new session variables
            session['user_id'] = user.id
            session['user_type'] = user.user_type
            session['email'] = user.email
            
            if user.user_type == 'manufacturer':
                manufacturer = Manufacturer.query.get(user.manufacturer_id)
                if manufacturer:
                    session['manufacturer_id'] = manufacturer.id
                    session['company_name'] = manufacturer.company_name
                    return redirect(url_for('manufacturer_dashboard'))
                else:
                    flash('Manufacturer details not found', 'error')
                    return redirect(url_for('login'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid email, password, or user type', 'error')
            
    return render_template('login.html')

@app.route('/user/dashboard')
def user_dashboard():
    if 'user_id' not in session or session['user_type'] != 'user':
        flash('Please login first', 'error')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('login'))
        
    return render_template('user_dashboard.html', user=user)

@app.route('/manufacturer/dashboard')
def manufacturer_dashboard():
    if 'user_id' not in session or session['user_type'] != 'manufacturer':
        flash('Please login first', 'error')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if not user or not user.manufacturer_id:
        flash('Manufacturer not found', 'error')
        return redirect(url_for('login'))
    
    manufacturer = Manufacturer.query.get(user.manufacturer_id)
    if not manufacturer:
        flash('Manufacturer details not found', 'error')
        return redirect(url_for('login'))
        
    return render_template('manufacturer_dashboard.html', 
                         manufacturer=manufacturer,
                         user=user)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('index'))

@app.route('/api/verify', methods=['POST'])
def verify_product():
    if 'user_id' not in session or session['user_type'] != 'user':
        return jsonify({'error': 'Unauthorized'}), 401

    if 'qr_code' not in request.files:
        return jsonify({'error': 'No QR code file provided'}), 400

    file = request.files['qr_code']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        # Read QR code content
        qr_content = file.read().decode('utf-8')
        product_data = json.loads(qr_content)
        
        # Validate product data
        is_valid = validate_product_data(product_data['product_id'], blockchain)
        
        if is_valid:
            # Add verification record
            verification = Verification(
                user_id=session['user_id'],
                product_id=product_data['product_id'],
                verification_date=datetime.utcnow()
            )
            db.session.add(verification)
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Product verified successfully',
                'product': product_data
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Invalid product'
            }), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products', methods=['POST'])
def add_product():
    if 'user_id' not in session or session['user_type'] != 'manufacturer':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        product = Product(
            manufacturer_id=session['user_id'],
            product_id=data['product_id'],
            product_type=data['product_type'],
            manufacturing_date=datetime.strptime(data['manufacturing_date'], '%Y-%m-%d'),
            expiry_date=datetime.strptime(data['expiry_date'], '%Y-%m-%d'),
            batch_number=data['batch_number'],
            manufacturing_unit=data['manufacturing_unit']
        )
        db.session.add(product)
        db.session.commit()

        # Generate QR code
        qr_data = {
            'product_id': product.product_id,
            'manufacturer_id': product.manufacturer_id,
            'manufacturing_date': product.manufacturing_date.isoformat(),
            'expiry_date': product.expiry_date.isoformat()
        }
        qr_code = generate_qr_code(qr_data)

        # Add to blockchain
        blockchain.new_transaction(
            sender=product.manufacturer_id,
            recipient=product.product_id,
            amount=1,
            product_data=qr_data
        )

        return jsonify({
            'status': 'success',
            'message': 'Product added successfully',
            'qr_code': qr_code
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.filter_by(product_id=product_id).first()
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    return jsonify({
        'product_id': product.product_id,
        'product_type': product.product_type,
        'manufacturing_date': product.manufacturing_date.isoformat(),
        'expiry_date': product.expiry_date.isoformat(),
        'batch_number': product.batch_number,
        'manufacturing_unit': product.manufacturing_unit
    })

@app.route('/manufacturer/products')
def view_products():
    if 'user_id' not in session or session['user_type'] != 'manufacturer':
        flash('Please login first', 'error')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if not user or not user.manufacturer_id:
        flash('Manufacturer not found', 'error')
        return redirect(url_for('login'))
    
    manufacturer = Manufacturer.query.get(user.manufacturer_id)
    if not manufacturer:
        flash('Manufacturer details not found', 'error')
        return redirect(url_for('login'))
    
    # Get all products for this manufacturer
    products = Product.query.filter_by(manufacturer_id=manufacturer.id).all()
    
    return render_template('view_products.html', 
                         manufacturer=manufacturer,
                         products=products)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# Add test manufacturer account
with app.app_context():
    # Check if test account already exists
    test_email = 'sushmitsharma8@gmail.com'
    existing_user = User.query.filter_by(email=test_email).first()
    
    if not existing_user:
        # Create test manufacturer
        test_manufacturer = Manufacturer(
            company_name='Test Company',
            contact_person='Sushmit Sharma',
            address='Test Address',
            contact='1234567890',
            registration_number='TEST123'
        )
        db.session.add(test_manufacturer)
        db.session.commit()

        # Create test user account
        test_user = User(
            email=test_email,
            password=generate_password_hash('abc@123'),
            user_type='manufacturer',
            manufacturer_id=test_manufacturer.id
        )
        db.session.add(test_user)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True, port=5002) 