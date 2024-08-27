from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Güvenli bir anahtar kullanın

# Veritabanı yapılandırması
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Veritabanı modelleri
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    password_hash = db.Column(db.String(150), nullable=False)
    avatar = db.Column(db.String(200), nullable=True, default='default_avatar.png')
    tasks = db.relationship('Task', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500), nullable=True)  # Yeni alan
    due_date = db.Column(db.DateTime, nullable=True)  # Yeni alan
    priority = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Open')  # Yeni status alanı
    completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<Task {self.id}: {self.task}>'

# Veritabanını başlat
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    tasks = Task.query.filter_by(user_id=user_id).all()
    return render_template('index.html', tasks=tasks, enumerate=enumerate)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')

        if not email:
            return "Email is required", 400  # E-posta zorunlu, eksikse hata ver

        user = User(username=username, email=email, first_name=first_name, last_name=last_name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['first_name'] = user.first_name
            session['last_name'] = user.last_name
            session['email'] = user.email
            session['avatar'] = user.avatar
            return redirect(url_for('index'))
        else:
            error = "Kullanıcı adı veya şifre hatalı"

    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/add', methods=['POST'])
def add():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    task = request.form.get('task').capitalize()  # Görev adının ilk harfini büyük yapar
    description = request.form.get('description')
    due_date = request.form.get('due_date')
    priority = request.form.get('priority')

    # İngilizce öncelikleri Türkçeye çevirme
    if priority == "High":
        priority = "Yüksek"
    elif priority == "Medium":
        priority = "Orta"
    elif priority == "Low":
        priority = "Düşük"

    if due_date:
        due_date = datetime.strptime(due_date, '%Y-%m-%d')

    new_task = Task(task=task, description=description, due_date=due_date, priority=priority, status='Open', user_id=user_id)
    db.session.add(new_task)
    db.session.commit()

    return redirect(url_for('index'))

@app.route('/change_status/<int:task_id>/<string:new_status>')
def change_status(task_id, new_status):
    task = Task.query.get_or_404(task_id)
    task.status = new_status
    task.completed = True if new_status == 'Completed' else False
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/complete/<int:task_id>')
def complete(task_id):
    task = Task.query.get_or_404(task_id)
    task.completed = True
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:task_id>')
def delete(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/tasks')
def all_tasks():
    tasks = Task.query.all()
    for task in tasks:
        print(f"ID: {task.id}, Task: {task.task}, Completed: {task.completed}")
    return "Check the terminal for task details"

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    user_id = session.get('user_id')

    if not user_id:
        return redirect(url_for('login'))  # Redirect to login if user is not logged in

    user = User.query.get(user_id)

    if not user:
        return redirect(url_for('login'))  # Redirect to login if user is not found

    if request.method == 'POST':
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.email = request.form.get('email')
        db.session.commit()
        # Add this line to trigger the alert on the front-end
        return "<script>alert('Profiliniz güncellenmiştir.'); window.location.href = '/profile';</script>"

    return render_template('profile.html', user=user)


@app.route('/check/<int:task_id>')
def check_task(task_id):
    task = Task.query.get(task_id)
    if task:
        return f"Task found: {task.task}, Completed: {task.completed}"
    else:
        return "Task not found", 404

@app.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    # Toplam görev sayısı
    total_tasks = Task.query.filter_by(user_id=user_id).count()

    # Tamamlanmış görev sayısı
    completed_tasks = Task.query.filter_by(user_id=user_id, status='Completed').count()

    # Bekleyen görev sayısı
    pending_tasks = Task.query.filter_by(user_id=user_id, status='Pending').count()

    # Devam eden görev sayısı
    ongoing_tasks = Task.query.filter_by(user_id=user_id, status='Ongoing').count()

    return render_template('dashboard.html', total_tasks=total_tasks, completed_tasks=completed_tasks,
                           pending_tasks=pending_tasks, ongoing_tasks=ongoing_tasks)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=1453)
