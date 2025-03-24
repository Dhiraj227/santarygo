from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from twilio.rest import Client
import random
import os
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Change this to a secure secret key

# Twilio credentials
TWILIO_ACCOUNT_SID = 'AC185e2e8df9e15e5f54bad236b5ccc6ac'
TWILIO_AUTH_TOKEN = '3b4e8ec087c760dd0bdf9a83282f7c0a'
TWILIO_PHONE_NUMBER = '+16073896731'

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

pad_otps = {}

@app.route('/')
def index():
    if 'authenticated' in session and session['authenticated']:
        return redirect(url_for('location'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone_number = request.form.get('phone_number')
        # Generate 6-digit OTP
        otp = str(random.randint(100000, 999999))
        session['otp'] = otp
        session['phone_number'] = phone_number
        
        # Send OTP via Twilio
        try:
            message = client.messages.create(
                body=f'Your OTP is: {otp}',
                from_=TWILIO_PHONE_NUMBER,
                to=phone_number
            )
            return redirect(url_for('verify_otp'))
        except Exception as e:
            return f"Error sending OTP: {str(e)}"
    
    return render_template('login.html')

@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        user_otp = request.form.get('otp')
        if user_otp == session.get('otp'):
            session['authenticated'] = True
            return redirect(url_for('location'))
        return "Invalid OTP"
    
    return render_template('verify_otp.html')

@app.route('/location')
def location():
    if not session.get('authenticated'):
        return redirect(url_for('login'))
    return render_template('location.html')

@app.route('/get-dispensers')
def get_dispensers():
    with open('dispensers.json', 'r') as file:
        dispensers = json.load(file)
    return jsonify(dispensers)

@app.route('/send-pad-otp', methods=['POST'])
def send_pad_otp():
    data = request.get_json()
    phone_number = data.get('phone_number')
    
    if not phone_number:
        return jsonify({'error': 'Phone number is required'}), 400
    
    # Generate 6-digit OTP
    otp = str(random.randint(100000, 999999))
    pad_otps[phone_number] = otp
    
    try:
        # Send OTP via Twilio
        message = client.messages.create(
            body=f'Hey your pad is being dispensed, use this OTP to access: {otp}',
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        return jsonify({'message': 'OTP sent successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/verify-pad-otp', methods=['POST'])
def verify_pad_otp():
    data = request.get_json()
    phone_number = data.get('phone_number')
    otp = data.get('otp')
    
    if not phone_number or not otp:
        return jsonify({'error': 'Phone number and OTP are required'}), 400
    
    stored_otp = pad_otps.get(phone_number)
    
    if stored_otp and stored_otp == otp:
        # Clear the OTP after successful verification
        pad_otps.pop(phone_number, None)

        # HERE CODE TO CONNECT TO HARDWARE
        print("HARDWARE CODE HERE")

        return jsonify({'message': 'OTP verified successfully'}), 200
    else:
        return jsonify({'error': 'Invalid OTP'}), 400

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/add-dispenser', methods=['POST'])
def add_dispenser():
    try:
        new_dispenser = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'latitude', 'longitude', 'address', 'pads_available']
        if not all(field in new_dispenser for field in required_fields):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400

        # Read existing dispensers
        with open('dispensers.json', 'r') as file:
            dispensers = json.load(file)

        # Add new dispenser
        dispensers.append(new_dispenser)

        # Write back to file
        with open('dispensers.json', 'w') as file:
            json.dump(dispensers, file, indent=4)

        return jsonify({'success': True}), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/logout')
def logout():
    session.clear()  # This will remove all session data
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)