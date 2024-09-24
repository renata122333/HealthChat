from flask import Blueprint, request, render_template
from model import make_prediction
import google.generativeai as genai

chatbot_routes = Blueprint('chatbot_routes', __name__)

questions = [
    {"question": "What is your name?", "range": "Text"},
    {"question": "What is your age?", "range": "18-100"},
    {"question": "What is your cholesterol level?", "range": "100-300"},
    {"question": "What is your systolic blood pressure?", "range": "90-180"},
    {"question": "What is your diastolic blood pressure?", "range": "60-120"},
    {"question": "What is your heart rate?", "range": "60-100"},
    {"question": "What is your BMI?", "range": "15-40"},
    {"question": "What is your triglycerides level?", "range": "50-500"},
    {"question": "How many hours per week do you exercise?", "range": "0-30"},
    {"question": "How many days per week are you physically active?", "range": "0-7"},
    {"question": "How many hours do you sleep per day?", "range": "4-12"},
    {"question": "How many hours per day do you spend being sedentary?", "range": "0-24"},
    {"question": "What is your sex?", "range": "Male/Female"},
    {"question": "Do you have diabetes?", "range": "Yes/No"},
    {"question": "Do you have a family history of heart disease?", "range": "Yes/No"},
    {"question": "Do you smoke?", "range": "Yes/No"},
    {"question": "Are you obese?", "range": "Yes/No"},
    {"question": "Do you consume alcohol?", "range": "Yes/No"},
    {"question": "How would you describe your diet?", "range": "Healthy/Unhealthy"},
    {"question": "Have you had any previous heart problems?", "range": "Yes/No"},
    {"question": "Do you take any medication regularly?", "range": "Yes/No"},
    {"question": "On a scale of 1-5, how would you rate your stress level?", "range": "1-5"},
    {"question": "What is your income level?", "range": "Low/Medium/High"}
]

user_responses = {}

genai.configure(api_key="AIzaSyAd0kEzSrkQ6fT4qGqyRxDY0CWolic7_N0")
model = genai.GenerativeModel('gemini-pro')


@chatbot_routes.route('/', methods=['GET', 'POST'])
def index():
    total_questions = len(questions)

    if request.method == 'POST':
        question_number = int(request.form.get('question_number', 0))
        response = request.form.get('response')

        if not validate_input(questions[question_number], response):
            return render_template('index.html', question=questions[question_number], question_number=question_number,
                                   total_questions=total_questions, error="Invalid input. Please check the range.")

        user_responses[questions[question_number]['question']] = response

        if question_number == total_questions - 1:
            risk, advice = make_prediction(user_responses)
            if risk == "Error":
                risk, advice = gemini_prediction(user_responses)
            return render_template('index.html', prediction=risk, advice=advice)

        return render_template('index.html', question=questions[question_number + 1],
                               question_number=question_number + 1, total_questions=total_questions)

    return render_template('index.html', question=questions[0], question_number=0, total_questions=total_questions)


def validate_input(question, response):
    if question['range'] == "Text":
        return True
    elif question['range'] in ["Yes/No", "Male/Female", "Healthy/Unhealthy", "Low/Medium/High"]:
        return response in question['range'].split('/')
    elif '-' in question['range']:
        min_val, max_val = map(float, question['range'].split('-'))
        try:
            value = float(response)
            return min_val <= value <= max_val
        except ValueError:
            return False
    return False


def gemini_prediction(responses):
    prompt = f"Based on the following health data, assess the risk of heart disease and provide advice: {responses}"
    response = model.generate_content(prompt)
    risk = "moderate"  # Default risk
    advice = response.text
    if "high risk" in response.text.lower():
        risk = "high"
    elif "low risk" in response.text.lower():
        risk = "low"
    return risk, advice

# Update app.py and model.py as needed
