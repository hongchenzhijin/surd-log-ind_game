from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os

# Try to import AI modules, but make them optional
try:
    from google.generativeai.client import configure
    from google.generativeai.generative_models import GenerativeModel
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print("Google Generative AI not available. AI features will be disabled.")

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random secret key

# --- AI Model Configuration ---
model = None
if AI_AVAILABLE:
    try:
        # Get API key from environment variable (more secure)
        api_key = "AIzaSyCIFc2MEBC0ezuFWD132neqjBo26EwBzvw"
        if api_key:
            configure(api_key=api_key)
            model = GenerativeModel('gemini-2.5-flash-lite-preview-06-17')
            print("AI Model initialized successfully.")
        else:
            print("GOOGLE_API_KEY environment variable not set. AI features disabled.")
    except Exception as e:
        print("AI Model could not be initialized. AI features will be disabled.")
        print(f"Error: {e}")

# --- Quiz Data ---
# In a real application, you might want to load this from a database
quizzes = {
    'surds': {
        1: {
            'question': 'Simplify √12',
            'options': ['2√3', '3√2', '4√3', '2√6'],
            'answer': '2√3'
        },
        2: {
            'question': 'Simplify √20 + √45',
            'options': ['5√5', '√65', '2√5 + 3√5', '5√10'],
            'answer': '5√5'
        },
        3: {
            'question': 'Rationalise the denominator of 1/√3',
            'options': ['√3/3', '√3', '1/3', '3/√3'],
            'answer': '√3/3'
        },
        4: {
            'question': 'Expand and simplify (2 + √3)(2 - √3)',
            'options': ['1', '7', '4 - 2√3', '4 + 2√3'],
            'answer': '1'
        },
        5: {
            'question': 'Simplify (√75)/ (√3)',
            'options': ['5', '√25', '√72', '25'],
            'answer': '5'
        }
    },
    'logarithms': {
        1: {
            'question': 'What is log₁₀(100)?',
            'options': ['1', '2', '10', '0'],
            'answer': '2'
        },
        2: {
            'question': 'If logₐ(b) = 3, what is b in terms of a?',
            'options': ['a^3', '3a', 'a/3', '3^a'],
            'answer': 'a^3'
        },
        3: {
            'question': 'What is log₂(8)?',
            'options': ['2', '3', '4', '8'],
            'answer': '3'
        },
        4: {
            'question': 'Simplify log₁₀(1000) - log₁₀(10)',
            'options': ['2', '3', '1', '0'],
            'answer': '2'
        },
        5: {
            'question': 'If log₃(x) = 4, what is x?',
            'options': ['12', '81', '64', '9'],
            'answer': '81'
        }
    },
    'indices': {
        1: {
            'question': 'Simplify 2^3 × 2^4',
            'options': ['2^7', '2^12', '2^1', '2^8'],
            'answer': '2^7'
        },
        2: {
            'question': 'What is (3^2)^3?',
            'options': ['3^5', '3^6', '6^3', '9^3'],
            'answer': '3^6'
        },
        3: {
            'question': 'Simplify 5^0',
            'options': ['0', '1', '5', 'undefined'],
            'answer': '1'
        },
        4: {
            'question': 'What is the value of 4^(-1)?',
            'options': ['-4', '1/4', '4', '0'],
            'answer': '1/4'
        },
        5: {
            'question': 'Simplify (2^4) / (2^2)',
            'options': ['2^2', '2^6', '2^8', '2^1'],
            'answer': '2^2'
        }
    }
}

exam_questions = {
    'surds': [
        {
            'question': 'A square garden has an area of 48 m². What is the exact length of one side in surd form?',
            'options': ['4√3 m', '6√2 m', '8 m', '√48 m'],
            'answer': '4√3 m'
        },
        {
            'question': 'A ladder of length 5√2 m rests against a wall, reaching a window 5 m above the ground. How far is the base of the ladder from the wall?',
            'options': ['5 m', '5√2 m', '5√3 m', '10 m'],
            'answer': '5 m'
        },
        {
            'question': 'The diagonal of a rectangle is 10 cm and one side is 6 cm. What is the exact length of the other side?',
            'options': ['8 cm', '√64 cm', '8√2 cm', '√28 cm'],
            'answer': '8 cm'
        }
    ],
    'logarithms': [
        {
            'question': 'The intensity I of an earthquake is given by I = log₁₀(E), where E is the energy released. If one earthquake releases 10,000 times more energy than another, how much greater is its intensity?',
            'options': ['2 units', '4 units', '10 units', '1 unit'],
            'answer': '4 units'
        },
        {
            'question': 'A scientist finds that the pH of a solution is 3. What is the hydrogen ion concentration [H⁺] in mol/L?',
            'options': ['1 × 10⁻³', '3 × 10⁻¹', '1 × 10³', '1 × 10⁻⁶'],
            'answer': '1 × 10⁻³'
        },
        {
            'question': 'The population of a bacteria culture doubles every hour. If the initial population is P₀, express the population after t hours using logarithms if the final population is 32P₀.',
            'options': ['t = log₂(32)', 't = log₃(32)', 't = 5', 't = log₁₀(32)'],
            'answer': 't = log₂(32)'
        }
    ],
    'indices': [
        {
            'question': 'A radioactive substance decays so that its mass halves every 3 years. If the initial mass is 80g, what will the mass be after 9 years?',
            'options': ['10g', '20g', '40g', '5g'],
            'answer': '10g'
        },
        {
            'question': 'The area of a square is 16x⁸. What is the length of one side?',
            'options': ['4x⁴', '8x²', '2x⁸', '16x⁴'],
            'answer': '4x⁴'
        },
        {
            'question': 'If 2ⁿ = 128, what is the value of n?',
            'options': ['7', '8', '6', '5'],
            'answer': '7'
        }
    ]
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/topic/<topic_name>')
def topic_map(topic_name):
    if 'progress' not in session:
        session['progress'] = {'surds': 0, 'logarithms': 0, 'indices': 0}

    return render_template('map.html', topic=topic_name, progress=session['progress'][topic_name])

@app.route('/topic/<topic_name>/stop/<int:stop_id>')
def stop(topic_name, stop_id):
    if stop_id == 1:
        # Tutorial for Surds
        if topic_name == 'surds':
            video_id = 'wzAotwNPhm8'  # GCSE Maths - What on Earth are Surds...
            return render_template('tutorial.html', topic=topic_name, stop_id=stop_id, video_id=video_id)
        elif topic_name == 'logarithms':
            video_id = 'kqVpPSzkTYA'  # Provided video ID for logarithms
            return render_template('tutorial.html', topic=topic_name, stop_id=stop_id, video_id=video_id)
        elif topic_name == 'indices':
            video_id = 'LkhPRz7Hocg'  # Provided video ID for indices
            return render_template('tutorial.html', topic=topic_name, stop_id=stop_id, video_id=video_id)
        else:
            # Placeholder for other topics' tutorials
            return render_template('tutorial.html', topic=topic_name, stop_id=stop_id, video_id=None)

    elif 2 <= stop_id <= 6:
        quiz_num = stop_id - 1
        if topic_name in quizzes and quiz_num in quizzes[topic_name]:
            quiz = quizzes[topic_name][quiz_num]
            return render_template('quiz.html', topic=topic_name, stop_id=stop_id, quiz=quiz, model_ready=(model is not None))
        else:
            # Handle cases where the quiz is not available
            return redirect(url_for('topic_map', topic_name=topic_name))

    elif stop_id == 7:
        if topic_name in exam_questions:
            exam = exam_questions[topic_name]
            return render_template('exam.html', topic=topic_name, exam=exam)
        else:
            # Handle cases where the exam is not available
            return redirect(url_for('topic_map', topic_name=topic_name))

    return redirect(url_for('topic_map', topic_name=topic_name))

@app.route('/submit_quiz/<topic_name>/<int:stop_id>', methods=['POST'])
def submit_quiz(topic_name, stop_id):
    user_answer = request.form.get('answer')
    quiz_num = stop_id - 1
    correct_answer = quizzes[topic_name][quiz_num]['answer']

    if user_answer == correct_answer:
        session['progress'][topic_name] = stop_id
        session.modified = True
        return redirect(url_for('results', topic_name=topic_name, stop_id=stop_id, result='correct'))
    else:
        return redirect(url_for('results', topic_name=topic_name, stop_id=stop_id, result='incorrect'))

@app.route('/results/<topic_name>/<int:stop_id>/<result>')
def results(topic_name, stop_id, result):
    return render_template('results.html', topic=topic_name, stop_id=stop_id, result=result)

@app.route('/complete_tutorial/<topic_name>', methods=['POST'])
def complete_tutorial(topic_name):
    if 'progress' not in session:
        session['progress'] = {'surds': 0, 'logarithms': 0, 'indices': 0}
    if session['progress'][topic_name] < 1:
        session['progress'][topic_name] = 1
        session.modified = True
    return redirect(url_for('topic_map', topic_name=topic_name))

@app.route('/submit_exam/<topic_name>', methods=['POST'])
def submit_exam(topic_name):
    exam = exam_questions[topic_name]
    total = len(exam)
    correct = 0
    for i, question in enumerate(exam):
        user_answer = request.form.get(f'answer{i}')
        if user_answer == question['answer']:
            correct += 1
    score = f"{correct} / {total}"
    return render_template('exam_result.html', topic=topic_name, score=score, total=total, correct=correct)

# --- NEW: AI Hint Generation Route ---
@app.route('/get_hint', methods=['POST'])
def get_hint():
    if not model:
        return jsonify({'hint': 'The AI hint feature is not available. Please check the server configuration.'})

    # Get the question from the frontend request
    data = request.get_json()
    question = data.get('question')

    if not question:
        return jsonify({'error': 'No question provided.'}), 400

    # Craft a precise prompt for the AI model
    prompt = f"""
    You are a friendly and helpful mathematics tutor for a student learning GCSE-level maths.
    A student is stuck on the following question and has asked for a hint.
    Your task is to provide a step-by-step hint to guide them to the solution.
    
    IMPORTANT RULES:
    1.  **Do not give the final answer.**
    2.  Break the problem down into simple, easy-to-follow steps.
    3.  Start with the first conceptual step needed to solve the problem.
    4.  Keep the tone encouraging and helpful.
    
    Question: "{question}"
    
    Provide your hint now.
    """
    
    try:
        response = model.generate_content(prompt)
        # Return the AI-generated text as a JSON response
        return jsonify({'hint': response.text})
    except Exception as e:
        print(f"Error generating content: {e}")
        return jsonify({'hint': 'Sorry, an error occurred while generating the hint.'}), 500

if __name__ == '__main__':
    app.run(debug=True)