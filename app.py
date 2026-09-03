import os
import secrets
import sys

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
os.chdir(BASE_DIR)

from flask import Flask, render_template, jsonify, request, send_file, abort, session
from config import Config
from models import db, Book, Category, User
from scanner import scan_books_directory
from mailer import generate_verification_code, send_verification_email
from chatbot import ask_arquimedes

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Inicializar Banco de Dados, criar usuario master e escanear
with app.app_context():
    db.create_all()

    # Criar usuario master padrao se ainda nao existir
    master = User.query.filter_by(username='oraculo').first()
    if not master:
        master_password = os.environ.get("MASTER_PASSWORD")
        generated = master_password is None
        if generated:
            master_password = secrets.token_urlsafe(12)

        master = User(
            username='oraculo',
            email='master@bibliotech.local',
            role='master',
            is_verified=True
        )
        master.set_password(master_password)
        db.session.add(master)
        db.session.commit()

        print("[BiblioTech] Usuario master 'oraculo' criado com sucesso.")
        if generated:
            print(f"[BiblioTech] Senha gerada automaticamente (guarde em local seguro): {master_password}")
            print("[BiblioTech] Defina MASTER_PASSWORD no .env para fixar essa senha em proximas reinstalacoes.")

    try:
        scan_books_directory(app)
    except Exception as e:
        print(f"Erro ao inicializar escaneamento: {e}")

# ------------------------------------------------------------------
# Helpers de sessao
# ------------------------------------------------------------------
def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

def is_master():
    u = get_current_user()
    return u is not None and u.role == 'master'

# ------------------------------------------------------------------
# Rotas principais
# ------------------------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')

# ------------------------------------------------------------------
# Autenticacao
# ------------------------------------------------------------------
@app.route('/api/auth/register', methods=['POST'])
def auth_register():
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not username or not email or not password:
        return jsonify({'error': 'Preencha todos os campos.'}), 400
    if len(password) < 6:
        return jsonify({'error': 'A senha deve ter pelo menos 6 caracteres.'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Este e-mail ja esta em uso.'}), 409
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Este nome de usuario ja esta em uso.'}), 409

    code = generate_verification_code()
    user = User(username=username, email=email, role='user', verification_code=code, is_verified=False)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    send_verification_email(email, code)
    return jsonify({'success': True, 'message': 'Codigo de confirmacao enviado para o e-mail.', 'email': email}), 201

@app.route('/api/auth/verify', methods=['POST'])
def auth_verify():
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    code = (data.get('code') or '').strip()

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': 'Usuario nao encontrado.'}), 404
    if user.is_verified:
        return jsonify({'error': 'Conta ja verificada.'}), 400
    if user.verification_code != code:
        return jsonify({'error': 'Codigo invalido. Tente novamente.'}), 401

    user.is_verified = True
    user.verification_code = None
    db.session.commit()

    session['user_id'] = user.id
    return jsonify({'success': True, 'user': user.to_dict()})

@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    user = User.query.filter(
        (User.username == username) | (User.email == username.lower())
    ).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Usuario ou senha incorretos.'}), 401
    if not user.is_verified:
        return jsonify({'error': 'Conta nao verificada. Verifique seu e-mail.', 'needs_verification': True, 'email': user.email}), 403

    session['user_id'] = user.id
    return jsonify({'success': True, 'user': user.to_dict()})

@app.route('/api/auth/logout', methods=['POST'])
def auth_logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/auth/me', methods=['GET'])
def auth_me():
    user = get_current_user()
    if not user:
        return jsonify({'logged_in': False}), 200
    return jsonify({'logged_in': True, 'user': user.to_dict()})

# ------------------------------------------------------------------
# Estatisticas
# ------------------------------------------------------------------
@app.route('/api/stats', methods=['GET'])
def get_stats():
    total_books = Book.query.count()
    total_size_mb = db.session.query(db.func.sum(Book.file_size_mb)).scalar() or 0
    read_books = Book.query.filter_by(status='Lido').count()
    reading_books = Book.query.filter_by(status='Lendo').count()
    total_categories = Category.query.count()
    favorites_count = Book.query.filter_by(is_favorite=True).count()

    stats = {
        'total_books': total_books,
        'read_books': read_books,
        'reading_books': reading_books,
        'total_categories': total_categories,
        'favorites_count': favorites_count,
        'is_master': is_master()
    }

    # Espaco em disco somente para master
    if is_master():
        stats['total_gb'] = round(total_size_mb / 1024, 2)

    return jsonify(stats)

# ------------------------------------------------------------------
# Categorias
# ------------------------------------------------------------------
@app.route('/api/categories', methods=['GET'])
def get_categories():
    categories = Category.query.order_by(Category.name).all()
    return jsonify([c.to_dict() for c in categories])

# ------------------------------------------------------------------
# Livros
# ------------------------------------------------------------------
@app.route('/api/books', methods=['GET'])
def get_books():
    category_id = request.args.get('category_id', type=int)
    search_query = request.args.get('search', type=str, default='')
    status_filter = request.args.get('status', type=str, default='')
    only_favorites = request.args.get('favorites', type=str, default='false').lower() == 'true'
    sort_by = request.args.get('sort', type=str, default='title')

    query = Book.query

    if category_id:
        query = query.filter(Book.category_id == category_id)
    if status_filter:
        query = query.filter(Book.status == status_filter)
    if only_favorites:
        query = query.filter(Book.is_favorite == True)
    if search_query:
        search_fmt = f"%{search_query}%"
        query = query.filter(
            (Book.title.like(search_fmt)) |
            (Book.author.like(search_fmt)) |
            (Book.summary.like(search_fmt))
        )

    if sort_by == 'size_desc':
        query = query.order_by(Book.file_size_mb.desc())
    elif sort_by == 'added_desc':
        query = query.order_by(Book.added_at.desc())
    else:
        query = query.order_by(Book.title.asc())

    books = query.all()
    return jsonify([b.to_dict() for b in books])

@app.route('/api/books/<int:book_id>', methods=['GET'])
def get_book_details(book_id):
    book = Book.query.get_or_404(book_id)
    return jsonify(book.to_dict())

@app.route('/api/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    book = Book.query.get_or_404(book_id)
    data = request.get_json() or {}

    if 'status' in data and data['status'] in ['Quero Ler', 'Lendo', 'Lido']:
        book.status = data['status']
    if 'is_favorite' in data:
        book.is_favorite = bool(data['is_favorite'])
    if 'rating' in data and isinstance(data['rating'], int):
        book.rating = max(1, min(5, data['rating']))

    db.session.commit()
    return jsonify(book.to_dict())

@app.route('/api/books/<int:book_id>/pdf', methods=['GET'])
def view_book_pdf(book_id):
    book = Book.query.get_or_404(book_id)
    if not os.path.exists(book.file_path):
        abort(404, description="Arquivo PDF nao encontrado no disco local.")

    return send_file(
        book.file_path,
        mimetype='application/pdf',
        as_attachment=False,
        download_name=book.original_filename
    )

# ------------------------------------------------------------------
# Chatbot Arquimedes
# ------------------------------------------------------------------
@app.route('/api/chat', methods=['POST'])
def chat_arquimedes():
    data = request.get_json() or {}
    message = (data.get('message') or '').strip()
    history = data.get('history') or []

    if not message:
        return jsonify({'error': 'Mensagem vazia.'}), 400

    books = Book.query.all()
    reply = ask_arquimedes(message, history, books)
    return jsonify({'reply': reply})

@app.route('/api/scan', methods=['POST'])
def trigger_scan():
    count = scan_books_directory(app)
    return jsonify({'success': True, 'new_books_count': count})

if __name__ == '__main__':
    print("==========================================================")
    print(" [BiblioTech] - Servidor de Biblioteca Online Iniciado")
    print(" -> Acesso Local: http://localhost:5000")
    print(" -> Acesso na Rede Interna: http://192.168.2.8:5000")
    print("==========================================================")
    app.run(host='0.0.0.0', port=5000, debug=False)
