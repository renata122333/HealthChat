from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify
from firebase_init import initialize_firebase
import firebase_admin
from firebase_admin import auth
import google.auth.exceptions
from datetime import timedelta

# Initialize Flask application
app = Flask(__name__)

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=60)
app.secret_key = 'your-secret-key'
# Set a secret key for session management

# Import and register chatbot blueprint
from chatbot import chatbot_routes

app.register_blueprint(chatbot_routes, url_prefix='/chatbot')

# Initialize Firebase
initialize_firebase()


# Verify ID Token and set session
@app.route('/verify_token', methods=['POST'])
def verify_token():
    token = request.json.get('token')

    try:
        # Verify the token using Firebase Admin SDK
        decoded_token = auth.verify_id_token(token)
        user_uid = decoded_token['uid']

        # Set the user ID in the session
        session['user'] = user_uid
        return jsonify({'success': True})
    except Exception as e:
        print(f"Token verification failed: {e}")
        return jsonify({'success': False})


# Route for signup page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        try:
            # Create a new user with Firebase
            user = auth.create_user(
                email=email,
                password=password,
                display_name=name
            )
            flash('Signup successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except firebase_admin.exceptions.FirebaseError as e:
            flash(f'Signup failed: {e}', 'error')

    return render_template('signup.html')


# Route for login page
@app.route('/', methods=['GET', 'POST'])
def login():
    return render_template('login.html')


# Home page route (protected)
@app.route('/home')
def home():
    if 'user' not in session:
        # User is not logged in, redirect to login page
        return redirect(url_for('login'))
    return render_template('home.html')


@app.route('/profile')
def profile():
    if 'user' not in session:
        flash('User session expired, please log in again.', 'error')
        return redirect(url_for('login'))

    try:
        # Debugging session
        print(f"Session User: {session.get('user')}")

        # Verify Firebase ID Token
        id_token = request.cookies.get('token')
        if not id_token:
            flash('Authentication token missing. Please log in again.', 'error')
            return redirect(url_for('login'))

        print(f"ID Token Retrieved: {id_token}")

        # Decoding token with some leeway to prevent minor timing issues
        decoded_token = auth.verify_id_token(id_token, leeway=5)
        uid = decoded_token.get('uid')

        if not uid:
            flash('Failed to verify user ID. Please log in again.', 'error')
            return redirect(url_for('login'))

        # Get user data from Firebase
        user = auth.get_user(uid)
        user_data = {
            'name': user.display_name or 'No Name Provided',
            'email': user.email,
            'profile_picture_url': user.photo_url or 'https://placehold.co/100x100'
        }

    except auth.InvalidIdTokenError:
        flash('Invalid authentication token. Please log in again.', 'error')
        return redirect(url_for('login'))
    except auth.ExpiredIdTokenError:
        flash('Authentication token has expired. Please log in again.', 'error')
        return redirect(url_for('login'))
    except Exception as e:
        print(f"Error in profile retrieval: {e}")
        flash(f'Failed to retrieve profile: {str(e)}', 'error')
        return redirect(url_for('login'))

    return render_template('profile.html', user=user_data)


@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user' not in session:
        return redirect(url_for('login'))

    user_id = session['user']

    name = request.form.get('name')
    surname = request.form.get('surname')
    dob = request.form.get('dob')
    email = request.form.get('email')
    description = request.form.get('description')
    profile_picture = request.files.get('profile_picture')

    try:
        # Update user profile information in Firebase
        auth.update_user(
            user_id,
            display_name=f"{name} {surname}",
            email=email
        )

        # Optionally, save the uploaded profile picture
        if profile_picture:
            # Save the profile picture and get the URL
            # e.g., upload to Firebase Storage and get the URL
            profile_picture_url = upload_to_storage(profile_picture)

        # Update user information in your database (if applicable)
        flash('Profile updated successfully!', 'success')
    except Exception as e:
        flash(f'Failed to update profile: {e}', 'error')

    return redirect(url_for('profile'))


# Logout route
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
