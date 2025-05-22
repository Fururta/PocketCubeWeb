from flask import Flask, jsonify, request, send_from_directory, redirect, url_for, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
import cube_logic
import random
import os

app = Flask(__name__, static_folder='static')
app.secret_key = 'supersegreta'  # Cambia questa stringa!
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(email=email).first():
            return 'Email già registrata!'
        user = User(email=email, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template_string('''
    <form method="post">
      Email: <input name="email" type="email"><br>
      Password: <input name="password" type="password"><br>
      <input type="submit" value="Registrati">
    </form>
    ''')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for('index'))
        return 'Credenziali errate!'
    return render_template_string('''
    <form method="post">
      Email: <input name="email" type="email"><br>
      Password: <input name="password" type="password"><br>
      <input type="submit" value="Login">
    </form>
    ''')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

lookup = cube_logic.build_lookup_table()

@app.route('/random')
@login_required
def random_cube():
    cube = random.choice(list(lookup.keys()))
    return jsonify({'cube': list(cube)})

@app.route('/move', methods=['POST'])
@login_required
def move_cube():
    data = request.json
    cube = bytes(data['cube'])
    move_idx = data['move']
    move = cube_logic.moves[move_idx]
    moved = bytes([cube[i] for i in move])
    return jsonify({'cube': list(moved)})

@app.route('/solve', methods=['POST'])
@login_required
def solve_cube():
    data = request.json
    cube = bytes(data['cube'])
    solution = []
    while move := lookup.get(cube):
        inverse = move
        for _ in range(3):
            inverse = bytes([inverse[i] for i in move])
        for idx, m in enumerate(cube_logic.moves):
            if m == inverse:
                break
        else:
            idx = -1
        solution.append(idx)
        cube = bytes([cube[i] for i in inverse])
    return jsonify({'solution': solution})

@app.route('/')
@login_required
def index():
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)