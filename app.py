import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from functools import wraps
from datetime import datetime

app = Flask(__name__, template_folder='.', static_folder='static')
app.secret_key = 'your_super_secret_key'

# --- Database Setup and Population Functions ---
def init_db():
    conn = sqlite3.connect('bitmentor.db')
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT, 
                    password TEXT, bio TEXT, profile_image_url TEXT)''')
    cur.execute('CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, name TEXT, description TEXT, badge TEXT)')
    cur.execute('CREATE TABLE IF NOT EXISTS enrollments (user_id INTEGER, course_id INTEGER, progress INTEGER, FOREIGN KEY(user_id) REFERENCES users(id), FOREIGN KEY(course_id) REFERENCES courses(id))')
    cur.execute('CREATE TABLE IF NOT EXISTS questions (id INTEGER PRIMARY KEY AUTOINCREMENT, course_id INTEGER, question_text TEXT, FOREIGN KEY(course_id) REFERENCES courses(id))')
    cur.execute('CREATE TABLE IF NOT EXISTS answers (id INTEGER PRIMARY KEY AUTOINCREMENT, question_id INTEGER, answer_text TEXT, is_correct INTEGER, FOREIGN KEY(question_id) REFERENCES questions(id))')
    cur.execute('CREATE TABLE IF NOT EXISTS threads (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, content TEXT, user_id INTEGER, timestamp DATETIME, FOREIGN KEY(user_id) REFERENCES users(id))')
    cur.execute('CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT, user_id INTEGER, thread_id INTEGER, timestamp DATETIME, FOREIGN KEY(user_id) REFERENCES users(id), FOREIGN KEY(thread_id) REFERENCES threads(id))')
    cur.execute('''CREATE TABLE IF NOT EXISTS lessons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, course_id INTEGER, module_num INTEGER,
                    lesson_num INTEGER, title TEXT, content TEXT, FOREIGN KEY(course_id) REFERENCES courses(id))''')
    cur.execute('''CREATE TABLE IF NOT EXISTS completed_lessons (
                    user_id INTEGER, lesson_id INTEGER, PRIMARY KEY(user_id, lesson_id),
                    FOREIGN KEY(user_id) REFERENCES users(id), FOREIGN KEY(lesson_id) REFERENCES lessons(id))''')
    conn.commit()
    conn.close()

def populate_courses():
    courses = [
        (1, 'Python for Beginners', "A comprehensive introduction to Python.", 'Pythonista'),
        (2, 'Java Fundamentals', "Learn the basics of object-oriented programming.", 'Java Apprentice'),
        (3, 'C++ Essentials', "Master the power and performance of C++.", 'C++ Pro')
    ]
    with sqlite3.connect("bitmentor.db") as con:
        cur = con.cursor()
        cur.executemany("INSERT OR IGNORE INTO courses (id, name, description, badge) VALUES (?,?,?,?)", courses)
        con.commit()
    print("Sample courses populated.")

def populate_lessons():
    all_lessons = [
        # Python Lessons (course_id=1)
        (1, 1, 1, 'What is Python?', 'Python is a high-level, interpreted programming language known for its readability and simple syntax.'),
        (1, 1, 2, 'Setting Up Your Environment', 'To start, you will need to install the Python interpreter from python.org and a code editor like VS Code.'),
        (1, 2, 1, 'Understanding Variables', 'Variables are containers for storing data values. In Python, a variable is created the moment you first assign a value to it.'),
        # Java Lessons (course_id=2)
        (2, 1, 1, 'What is Java?', 'Java is a class-based, object-oriented programming language that is designed to have as few implementation dependencies as possible.'),
        (2, 1, 2, 'The JDK and JRE', 'The Java Development Kit (JDK) is a software development environment used for developing Java applications.'),
        (2, 2, 1, 'Variables and Data Types', 'In Java, every variable has a data type, such as int or String.'),
        # C++ Lessons (course_id=3)
        (3, 1, 1, 'Introduction to C++', 'C++ is a powerful, high-performance programming language developed by Bjarne Stroustrup.'),
        (3, 1, 2, 'Setting up a Compiler', 'To write and run C++ code, you need a C++ compiler like G++ or Clang.'),
        (3, 2, 1, 'Basic Syntax and Structure', 'A C++ program consists of various elements including variables, functions, and control structures.')
    ]
    with sqlite3.connect("bitmentor.db") as con:
        cur = con.cursor()
        cur.executemany("INSERT OR IGNORE INTO lessons (course_id, module_num, lesson_num, title, content) VALUES (?,?,?,?,?)", all_lessons)
        con.commit()
    print("Sample lessons for all courses populated.")

def populate_tests():
    with sqlite3.connect("bitmentor.db") as con:
        cur = con.cursor()
        cur.execute("INSERT OR IGNORE INTO questions (id, course_id, question_text) VALUES (?,?,?)", (1, 1, "What does the 'print()' function do in Python?"))
        answers_q1 = [(1, "Prints output to the console", 1),(1, "Asks for user input", 0),(1, "Creates a new variable", 0)]
        cur.executemany("INSERT OR IGNORE INTO answers (question_id, answer_text, is_correct) VALUES (?,?,?)", answers_q1)
        cur.execute("INSERT OR IGNORE INTO questions (id, course_id, question_text) VALUES (?,?,?)", (2, 1, "Which data type is used for text?"))
        answers_q2 = [(2, "Integer", 0),(2, "String", 1),(2, "Boolean", 0)]
        cur.executemany("INSERT OR IGNORE INTO answers (question_id, answer_text, is_correct) VALUES (?,?,?)", answers_q2)
        con.commit()
    print("Sample tests populated.")

def populate_forum():
    with sqlite3.connect("bitmentor.db") as con:
        cur = con.cursor()
        cur.execute("INSERT OR IGNORE INTO threads (id, title, content, user_id, timestamp) VALUES (?,?,?,?,?)", (1, "Python loops help", "...", 1, datetime.now()))
        cur.execute("INSERT OR IGNORE INTO posts (content, user_id, thread_id, timestamp) VALUES (?,?,?,?)",("Use range()...", 2, 1, datetime.now())); con.commit()

def enroll_sample_user():
    enrollments = [(1, 1, 0),(1, 2, 5)]
    with sqlite3.connect("bitmentor.db") as con:
        cur = con.cursor(); cur.executemany("INSERT OR IGNORE INTO enrollments (user_id, course_id, progress) VALUES (?,?,?)", enrollments); con.commit()

# --- Login Required Decorator ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session: return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

# --- Page Routes ---
@app.route('/')
def index(): return redirect(url_for('login_page'))
@app.route('/signup')
def signup_page(): return render_template('signup.html')
@app.route('/login')
def login_page(): return render_template('login.html')
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    with sqlite3.connect("bitmentor.db") as con:
        con.row_factory = sqlite3.Row; cur = con.cursor()
        cur.execute("SELECT c.name, c.description, e.progress FROM courses c JOIN enrollments e ON c.id = e.course_id WHERE e.user_id = ?", (user_id,)); enrolled_courses = cur.fetchall()
    return render_template('dashboard.html', user_name=session.get('user_name'), courses=enrolled_courses)

@app.route('/courses')
@login_required
def courses_page():
    with sqlite3.connect("bitmentor.db") as con:
        con.row_factory = sqlite3.Row; cur = con.cursor()
        cur.execute("SELECT * FROM courses"); all_courses = cur.fetchall()
    return render_template('courses.html', user_name=session.get('user_name'), courses=all_courses)

@app.route('/course/<int:course_id>')
@login_required
def course_detail_page(course_id):
    with sqlite3.connect("bitmentor.db") as con:
        con.row_factory = sqlite3.Row; cur = con.cursor()
        cur.execute("SELECT * FROM courses WHERE id = ?", (course_id,)); course = cur.fetchone()
        cur.execute("SELECT * FROM lessons WHERE course_id = ? ORDER BY module_num, lesson_num", (course_id,)); lessons = cur.fetchall()
    return render_template('course-detail.html', user_name=session.get('user_name'), course=course, lessons=lessons)

@app.route('/profile')
@login_required
def profile_page():
    user_id = session['user_id']
    stats = {}
    with sqlite3.connect("bitmentor.db") as con:
        con.row_factory = sqlite3.Row; cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE id = ?", (user_id,)); user_data = cur.fetchone()
        cur.execute("SELECT COUNT(*) as count FROM enrollments WHERE user_id = ?", (user_id,)); stats['enrolled_courses'] = cur.fetchone()['count']
        cur.execute("SELECT COUNT(*) as count FROM threads WHERE user_id = ?", (user_id,)); stats['forum_threads'] = cur.fetchone()['count']
        cur.execute("SELECT COUNT(*) as count FROM posts WHERE user_id = ?", (user_id,)); stats['forum_posts'] = cur.fetchone()['count']
    return render_template('profile.html', user=user_data, stats=stats)

@app.route('/scheduler', methods=['GET', 'POST'])
@login_required
def scheduler_page():
    schedule = None
    if request.method == 'POST':
        goal = request.form['goal']; hours = int(request.form['hours']); schedule = []
        course_name = "Tech";
        if goal == 'python': course_name = "Python"
        elif goal == 'java': course_name = "Java"
        if hours <= 3: schedule.extend([f"Wed: 2 lessons in {course_name}.", f"Fri: Review lessons."])
        elif hours <= 7: schedule.extend([f"Mon: 2 lessons.", f"Wed: 2 more lessons.", f"Fri: Small project."])
        else: schedule.extend([f"Mon/Tue: 4 lessons.", f"Wed/Thu: Mini-project.", f"Fri: Mock test."])
    return render_template('scheduler.html', user_name=session.get('user_name'), schedule=schedule)

@app.route('/mock-tests')
@login_required
def mock_tests_page(): return render_template('mock-tests.html', user_name=session.get('user_name'))

@app.route('/start-test/<int:course_id>')
@login_required
def start_test(course_id):
    with sqlite3.connect("bitmentor.db") as con:
        con.row_factory = sqlite3.Row; cur = con.cursor()
        cur.execute("SELECT * FROM questions WHERE course_id = ?", (course_id,)); questions_raw = cur.fetchall()
        questions = []
        for q in questions_raw:
            question_dict = dict(q); cur.execute("SELECT * FROM answers WHERE question_id = ?", (question_dict['id'],)); question_dict['answers'] = cur.fetchall(); questions.append(question_dict)
    return render_template('test-player.html', user_name=session.get('user_name'), questions=questions, course_id=course_id)

@app.route('/forum')
@login_required
def forum_page():
    with sqlite3.connect("bitmentor.db") as con:
        con.row_factory = sqlite3.Row; cur = con.cursor()
        cur.execute("SELECT t.id, t.title, t.timestamp, u.name as author_name FROM threads t JOIN users u ON t.user_id = u.id ORDER BY t.timestamp DESC"); threads_raw = cur.fetchall()
        threads = []
        for thread_raw in threads_raw:
            thread = dict(thread_raw)
            if thread['timestamp']: thread['timestamp'] = datetime.strptime(thread['timestamp'], '%Y-%m-%d %H:%M:%S.%f')
            threads.append(thread)
    return render_template('forum.html', user_name=session.get('user_name'), threads=threads)

@app.route('/thread/<int:thread_id>')
@login_required
def thread_page(thread_id):
    with sqlite3.connect("bitmentor.db") as con:
        con.row_factory = sqlite3.Row; cur = con.cursor()
        cur.execute("SELECT t.*, u.name as author_name FROM threads t JOIN users u ON t.user_id = u.id WHERE t.id = ?", (thread_id,)); thread_raw = cur.fetchone()
        thread = dict(thread_raw)
        if thread['timestamp']: thread['timestamp'] = datetime.strptime(thread['timestamp'], '%Y-%m-%d %H:%M:%S.%f')
        cur.execute("SELECT p.*, u.name as author_name FROM posts p JOIN users u ON p.user_id = u.id WHERE p.thread_id = ? ORDER BY p.timestamp ASC", (thread_id,)); posts_raw = cur.fetchall()
        posts = []
        for post_raw in posts_raw:
            post = dict(post_raw)
            if post['timestamp']: post['timestamp'] = datetime.strptime(post['timestamp'], '%Y-%m-%d %H:%M:%S.%f')
            posts.append(post)
    return render_template('thread.html', user_name=session.get('user_name'), thread=thread, posts=posts, thread_id=thread_id)

@app.route('/new-thread')
@login_required
def new_thread_page(): return render_template('create-thread.html', user_name=session.get('user_name'))

# --- API Routes ---
@app.route('/register', methods=['POST'])
def register_user():
    name = request.form['fullname']; email = request.form['email']; password = request.form['password']
    with sqlite3.connect("bitmentor.db") as con:
        cur = con.cursor(); cur.execute("INSERT INTO users (name, email, password) VALUES (?,?,?)", (name, email, password)); con.commit(); new_user_id = cur.lastrowid
    session['user_id'] = new_user_id; session['user_name'] = name
    return redirect(url_for('dashboard'))

@app.route('/auth', methods=['POST'])
def auth_user():
    email = request.form['email']; password = request.form['password']
    with sqlite3.connect("bitmentor.db") as con:
        con.row_factory = sqlite3.Row; cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password)); user = cur.fetchone()
        if user:
            session['user_id'] = user['id']; session['user_name'] = user['name']
            return redirect(url_for('dashboard'))
        else: return "Invalid email or password."

@app.route('/enroll/<int:course_id>')
@login_required
def enroll(course_id):
    user_id = session['user_id']
    with sqlite3.connect("bitmentor.db") as con:
        cur = con.cursor(); cur.execute("INSERT OR IGNORE INTO enrollments (user_id, course_id, progress) VALUES (?,?,?)", (user_id, course_id, 0)); con.commit()
    return redirect(url_for('dashboard'))

@app.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    user_id = session['user_id']; new_name = request.form['fullname']; new_bio = request.form['bio']
    with sqlite3.connect("bitmentor.db") as con:
        cur = con.cursor(); cur.execute("UPDATE users SET name = ?, bio = ? WHERE id = ?", (new_name, new_bio, user_id)); con.commit()
    session['user_name'] = new_name
    return redirect(url_for('profile_page'))

@app.route('/create-thread', methods=['POST'])
@login_required
def create_thread():
    title = request.form['title']; content = request.form['content']; user_id = session['user_id']
    with sqlite3.connect("bitmentor.db") as con:
        cur = con.cursor(); cur.execute("INSERT INTO threads (title, content, user_id, timestamp) VALUES (?,?,?,?)", (title, content, user_id, datetime.now())); con.commit()
    return redirect(url_for('forum_page'))

@app.route('/thread/<int:thread_id>/reply', methods=['POST'])
@login_required
def post_reply(thread_id):
    content = request.form['content']; user_id = session['user_id']
    with sqlite3.connect("bitmentor.db") as con:
        cur = con.cursor(); cur.execute("INSERT INTO posts (content, user_id, thread_id, timestamp) VALUES (?,?,?,?)", (content, user_id, thread_id, datetime.now())); con.commit()
    return redirect(url_for('thread_page', thread_id=thread_id))

@app.route('/submit-test/<int:course_id>', methods=['POST'])
@login_required
def submit_test(course_id):
    submitted_answer_ids = [v for k, v in request.form.items() if k.startswith('question_')]
    if not submitted_answer_ids: return "You did not answer any questions.", 400
    with sqlite3.connect("bitmentor.db") as con:
        con.row_factory = sqlite3.Row; cur = con.cursor(); placeholders = ','.join(['?'] * len(submitted_answer_ids))
        cur.execute(f"SELECT COUNT(*) FROM answers WHERE id IN ({placeholders}) AND is_correct = 1", submitted_answer_ids); correct_answers_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM questions WHERE course_id = ?", (course_id,)); total_questions = cur.fetchone()[0]
    score = int((correct_answers_count / total_questions) * 100) if total_questions > 0 else 0
    return render_template('results.html', user_name=session.get('user_name'), score=score)

if __name__ == '__main__':
    app.run(debug=True)
