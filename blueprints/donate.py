# blueprints/donate.py
import razorpay
from flask import Blueprint, render_template, request, jsonify, session
from models import db, Donation, User
from datetime import datetime

donate_bp = Blueprint('donate', __name__)

# Initialize Razorpay client
import os
razorpay_client = razorpay.Client(
    auth=(os.getenv('RAZORPAY_KEY_ID'), os.getenv('RAZORPAY_KEY_SECRET'))
)


@donate_bp.route('/donate')
def donate_page():
    """Donation page"""
    return render_template('donate.html', 
                         razorpay_key_id=os.getenv('RAZORPAY_KEY_ID'))


@donate_bp.route('/api/create-donation-order', methods=['POST'])
def create_donation_order():
    """Create Razorpay order for donation"""
    try:
        data = request.get_json()
        amount = float(data.get('amount', 0))
        donor_name = data.get('name', '').strip()
        donor_email = data.get('email', '').strip()
        donor_mobile = data.get('mobile', '').strip()
        message = data.get('message', '').strip()
        
        # Validate amount (min ₹10, max ₹100000)
        if amount < 10:
            return jsonify({'success': False, 'message': 'Minimum donation amount is ₹10'})
        if amount > 100000:
            return jsonify({'success': False, 'message': 'Maximum donation amount is ₹1,00,000'})
        
        # Convert to paise
        amount_in_paise = int(amount * 100)
        
        # Create Razorpay order
        order_data = {
            'amount': amount_in_paise,
            'currency': 'INR',
            'receipt': f'donation_{datetime.utcnow().strftime("%Y%m%d%H%M%S")}',
            'notes': {
                'donor_name': donor_name,
                'donor_email': donor_email,
                'donor_mobile': donor_mobile,
                'message': message
            }
        }
        
        razorpay_order = razorpay_client.order.create(data=order_data)
        
        # Save donation record
        donation = Donation(
            user_id=session.get('user_id'),
            donor_name=donor_name or 'Anonymous',
            donor_email=donor_email or '',
            donor_mobile=donor_mobile or '',
            amount=amount,
            currency='INR',
            order_id=razorpay_order['id'],
            status='pending',
            message=message or ''
        )
        db.session.add(donation)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'order_id': razorpay_order['id'],
            'amount': amount_in_paise,
            'currency': 'INR',
            'donation_id': donation.id
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@donate_bp.route('/api/verify-donation', methods=['POST'])
def verify_donation():
    """Verify donation payment"""
    try:
        data = request.get_json()
        
        # Verify signature
        params_dict = {
            'razorpay_order_id': data.get('razorpay_order_id'),
            'razorpay_payment_id': data.get('razorpay_payment_id'),
            'razorpay_signature': data.get('razorpay_signature')
        }
        
        razorpay_client.utility.verify_payment_signature(params_dict)
        
        # Get payment details
        payment = razorpay_client.payment.fetch(data.get('razorpay_payment_id'))
        
        # Update donation record
        donation = Donation.query.filter_by(order_id=data.get('razorpay_order_id')).first()
        
        if donation:
            donation.status = 'success'
            donation.payment_id = data.get('razorpay_payment_id')
            donation.payment_method = payment.get('method', 'Unknown')
            db.session.commit()
        
        return jsonify({'success': True, 'message': 'Payment verified successfully!'})
        
    except razorpay.errors.SignatureVerificationError:
        # Payment failed
        donation = Donation.query.filter_by(order_id=data.get('razorpay_order_id')).first()
        if donation:
            donation.status = 'failed'
            db.session.commit()
        
        return jsonify({'success': False, 'message': 'Payment verification failed!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})