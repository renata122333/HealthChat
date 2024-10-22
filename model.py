import firebase_admin
from firebase_admin import credentials, db
import numpy as np
import tensorflow as tf
from sklearn.preprocessing import StandardScaler, LabelEncoder
from firebase_init import initialize_firebase  # Import your Firebase initialization

# Initialize Firebase before any Firebase service is accessed
initialize_firebase()


model = tf.keras.models.load_model('heart_attack_model.keras')
firebase_ref = db.reference('responses')
numerical_features = ['Age', 'Cholesterol', 'Systolic_BP', 'Diastolic_BP', 'Heart Rate', 'BMI', 'Triglycerides',
                      'Exercise Hours Per Week', 'Physical Activity Days Per Week', 'Sleep Hours Per Day',
                      'Sedentary Hours Per Day']
categorical_features = ['Sex', 'Diabetes', 'Family History', 'Smoking', 'Obesity', 'Alcohol Consumption', 'Diet',
                        'Previous Heart Problems', 'Medication Use', 'Stress Level', 'Income']

scaler = StandardScaler()
label_encoders = {feature: LabelEncoder() for feature in categorical_features}


def make_prediction(responses):
    try:
        user_name = responses.pop("What is your name?")
        features = []
        for feature in numerical_features + categorical_features:
            features.append(responses[feature])

        features = np.array(features).reshape(1, -1)

        prediction = model.predict(features)[0][0]
        risk = "high" if prediction > 0.7 else "moderate" if prediction > 0.4 else "low"
        advice = "Consult a doctor immediately." if risk == "high" else "Consider lifestyle changes and consult a doctor." if risk == "moderate" else "Maintain your healthy lifestyle."

        save_to_firebase(user_name, responses, prediction, risk, advice)
        return risk, advice
    except Exception as e:
        print(f"Error making prediction: {e}")
        return "Error", "There was an issue processing your data."


# Function to save user input and prediction to Firebase
def save_to_firebase(user_name, responses, prediction, risk, advice):
    try:
        # Create a reference for the specific user in the database
        user_ref = firebase_ref.child(user_name)

        # Prepare data to be saved
        user_data = {
            'responses': responses,  # User's input
            'prediction': float(prediction),  # Model prediction (probability)
            'risk': risk,  # Risk level (high/moderate/low)
            'advice': advice  # Advice provided
        }

        # Save data under the user's reference
        user_ref.push(user_data)
    except Exception as e:
        print(f"Error saving to Firebase: {e}")