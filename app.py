import logging
import os

from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify
from werkzeug.security import check_password_hash

from firebase_init import initialize_firebase
import firebase_admin
from firebase_admin import auth, db
import google.auth.exceptions
from datetime import timedelta

# Initialize Flask application
app = Flask(__name__)
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=60)
app.secret_key = os.urandom(24)

# Import and register chatbot blueprint
from chatbot import chatbot_routes

app.register_blueprint(chatbot_routes, url_prefix='/chatbot')

# Initialize Firebase
initialize_firebase()
# Reference to the Firebase database
ref = db.reference()

# Home page route (protected)
@app.route('/home')
def home():
    if 'user' not in session:
        # Redirect to login page if not logged in
        flash("You must be logged in to access the home page.", "error")
        return redirect(url_for('login'))

    # Render the home page if the user is logged in
    return render_template('home.html')


@app.route('/verify_token', methods=['POST'])
def verify_token():
    token = request.json.get('token')

    try:
        # Verify the token using Firebase Admin SDK
        decoded_token = auth.verify_id_token(token)
        user_uid = decoded_token['uid']

        # Optionally, you can set the session or do further processing
        session['user'] = user_uid
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        surname = request.form.get('surname')
        dob = request.form.get('dob')
        description = request.form.get('description')

        try:
            # Create a new user in Firebase Authentication
            user = auth.create_user(email=email, password=password)
            # Save additional user details in Firebase Realtime Database
            user_ref = db.reference(f'users/{user.uid}')
            user_ref.set({
                'name': name,
                'surname': surname,
                'dob': dob,
                'email': email,
                'description': description,
                'profile_picture_url': 'https://placehold.co/100x100'
            })

            flash('Signup successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Error during signup: {e}', 'error')

    return render_template('signup.html')


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            # Get user data from Firebase Authentication by email
            user = auth.get_user_by_email(email)

            # Retrieve user's password hash from Firebase Realtime Database
            user_ref = db.reference(f'users/{user.uid}')
            user_data = user_ref.get()

            if 'password' not in user_data:
                flash('Password not found. Please signup again.', 'error')
                return redirect(url_for('signup'))

            # Check if the password matches (if stored securely in a hashed form)
            if check_password_hash(user_data['password'], password):
                # Store the user session
                session['user'] = user_data
                session['user_id'] = user.uid
                flash("Login successful!", "success")
                return redirect(url_for('home'))  # Redirect to the home page
            else:
                flash('Invalid credentials. Please try again.', 'error')

        except firebase_admin.auth.UserNotFoundError:
            flash("Email not found, please sign up first", "error")
        except Exception as e:
            flash(f"Error during login: {e}", 'error')

    return render_template('login.html')


@app.route('/profile_page', methods=['GET', 'POST'])
def profile_page():
    if 'user' not in session:
        return redirect(url_for('login'))

    user_uid = session['user']
    user_ref = db.reference(f'users/{user_uid}')
    user = user_ref.get()

    if request.method == 'POST':
        # Update profile information in Firebase Realtime Database
        user_ref.update({
            'name': request.form.get('name'),
            'surname': request.form.get('surname'),
            'dob': request.form.get('dob'),
            'email': request.form.get('email'),
            'description': request.form.get('description')
        })
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('profile_page'))

    return render_template('profile_page.html', user=user)


# Logout route
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
