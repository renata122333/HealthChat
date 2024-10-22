import logging
import os
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, send_file, session
from werkzeug.security import generate_password_hash, check_password_hash
from firebase_init import initialize_firebase
import firebase_admin
from firebase_admin import auth, db, storage
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import timedelta
from werkzeug.utils import secure_filename
import tempfile
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
import google.generativeai as genai

# Initialize Flask application
db_ref, bucket = initialize_firebase()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=60)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Firebase
db_ref, bucket = initialize_firebase()

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)


# Import and register chatbot blueprint
from chatbot import chatbot_routes
app.register_blueprint(chatbot_routes, url_prefix='/chatbot')


class User(UserMixin):
    def __init__(self, uid, email, name, surname):
        self.id = uid
        self.email = email
        self.name = name
        self.surname = surname

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"Server Error: {error}")
    return "An internal error occurred", 500

@login_manager.user_loader
def load_user(user_id):
    user_data = db.reference(f'users/{user_id}').get()
    if user_data:
        return User(user_id, user_data['email'], user_data['name'], user_data['surname'])
    return None


@app.route('/home')
@login_required
def home():
    return render_template('home.html', user=current_user)


@app.route('/verify_token', methods=['POST'])
def verify_token():
    token = request.json.get('token')
    try:
        decoded_token = auth.verify_id_token(token)
        user_uid = decoded_token['uid']
        user = load_user(user_uid)
        if user:
            login_user(user)
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
            user = auth.create_user(email=email, password=password)
            hashed_password = generate_password_hash(password)
            user_ref = db.reference(f'users/{user.uid}')
            user_ref.set({
                'name': name,
                'surname': surname,
                'dob': dob,
                'email': email,
                'description': description,
                'password': hashed_password,
                'profile_picture_url': 'https://placehold.co/100x100'
            })
            flash('Signup successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Error during signup: {e}', 'error')
    return render_template('signup.html')


@app.route('/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        app.logger.info(f"Login attempt for email: {email}")
        try:
            user = auth.get_user_by_email(email)
            user_ref = db.reference(f'users/{user.uid}')
            user_data = user_ref.get()
            if user_data:
                stored_password = user_data.get('password')
                if stored_password and check_password_hash(stored_password, password):
                    user_obj = User(user.uid, email, user_data['name'], user_data['surname'])
                    login_user(user_obj)
                    session['user'] = user.uid  # Add this line
                    app.logger.info(f"User {email} logged in successfully")
                    return redirect(url_for('home'))
                else:
                    app.logger.warning(f"Invalid password for user {email}")
                    flash('Invalid email or password', 'error')
            else:
                app.logger.warning(f"No user data found in database for {email}")
                flash('User data not found', 'error')
        except auth.UserNotFoundError:
            app.logger.warning(f"No user found with email {email}")
            flash('Invalid email or password', 'error')
        except Exception as e:
            app.logger.error(f"Login error for {email}: {str(e)}")
            flash('An error occurred during login', 'error')
    return render_template('login.html')


class UpdateUserForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    surname = StringField('Surname', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    dob = StringField('Date of Birth')
    description = TextAreaField('Description')
    profile_pic = FileField('Profile Picture')
    med_recs = FileField('Medical Records')
    submit = SubmitField('Update Profile')


@app.route('/profile_page', methods=['GET', 'POST'])
@login_required
def profile_page():
    form = UpdateUserForm()
    user_ref = db.reference(f'users/{current_user.id}')
    user = user_ref.get()

    if form.validate_on_submit():
        # Update user information
        user_ref.update({
            'name': form.name.data,
            'surname': form.surname.data,
            'dob': form.dob.data,
            'email': form.email.data,
            'description': form.description.data
        })

        # Handle profile picture upload
        if form.profile_pic.data:
            profile_pic = form.profile_pic.data
            filename = secure_filename(profile_pic.filename)
            blob = bucket.blob(f'profile_pics/{current_user.id}/{filename}')
            blob.upload_from_file(profile_pic, content_type=profile_pic.content_type)
            blob.make_public()
            user_ref.update({'profile_picture_url': blob.public_url})

        # Handle medical records upload
        if form.med_recs.data:
            med_recs = form.med_recs.data
            filename = secure_filename(med_recs.filename)
            blob = bucket.blob(f'medical_records/{current_user.id}/{filename}')
            blob.upload_from_file(med_recs, content_type=med_recs.content_type)
            med_records = user.get('medical_records', [])
            med_records.append({
                'filename': filename,
                'path': f'medical_records/{current_user.id}/{filename}'
            })
            user_ref.update({'medical_records': med_records})

        flash('Profile updated successfully.', 'success')
        return redirect(url_for('profile_page'))

    elif request.method == 'GET':
        form.name.data = user.get('name')
        form.surname.data = user.get('surname')
        form.email.data = user.get('email')
        form.dob.data = user.get('dob')
        form.description.data = user.get('description')

    med_records = user.get('medical_records', [])
    return render_template('profile_page.html', form=form, user=user, med_records=med_records)


@app.route('/download_medical_record/<path:record_path>')
@login_required
def download_medical_record(record_path):
    try:
        blob = bucket.blob(record_path)
        _, temp_local_filename = tempfile.mkstemp()

        # Download the file to a temporary file
        blob.download_to_filename(temp_local_filename)

        # Send the file to the user
        return send_file(temp_local_filename, as_attachment=True, attachment_filename=os.path.basename(record_path))
    except Exception as e:
        app.logger.error(f"Error downloading file: {str(e)}")
        flash('Error downloading file', 'error')
        return redirect(url_for('profile_page'))
    finally:
        # Clean up the temporary file
        os.remove(temp_local_filename)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()  # Add this line
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


def check_password_hashing():
    users_ref = db.reference('users')
    users = users_ref.get()

    if not users:
        logging.warning("No users found in the database.")
        return

    for uid, user_data in users.items():
        email = user_data.get('email', 'No email')
        password = user_data.get('password')
        logging.info(f"User data for {email}: {user_data}")
        if not password:
            logging.warning(f"No password found for user: {email}")
        else:
            if password.startswith('pbkdf2:sha256:') or password.startswith('$2b$') or len(password) > 50:
                logging.info(f"Hashed password found for user: {email}")
            else:
                logging.warning(f"Plaintext password found for user: {email}")

    logging.info(f"Total users checked: {len(users)}")


if __name__ == '__main__':
    # Check existing password hashing
    check_password_hashing()

    # Run the Flask application
    app.run(debug=True)
