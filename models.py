from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    icon = db.Column(db.String(50), default="folder")
    color = db.Column(db.String(50), default="#6366f1")

    books = db.relationship('Book', backref='category_rel', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'icon': self.icon,
            'color': self.color,
            'book_count': len(self.books)
        }

class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.Text, nullable=False, unique=True)
    file_size_mb = db.Column(db.Float, nullable=False)
    file_format = db.Column(db.String(10), default="PDF")
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    category_name = db.Column(db.String(100), default="Geral")
    author = db.Column(db.String(200), default="Autor Desconhecido")
    summary = db.Column(db.Text, nullable=True)
    topics = db.Column(db.String(500), nullable=True)
    cover_filename = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), default="Quero Ler")
    is_favorite = db.Column(db.Boolean, default=False)
    rating = db.Column(db.Integer, default=5)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'original_filename': self.original_filename,
            'file_path': self.file_path,
            'file_size_mb': round(self.file_size_mb, 2),
            'file_format': self.file_format,
            'category_id': self.category_id,
            'category_name': self.category_name,
            'author': self.author,
            'summary': self.summary,
            'topics': [t.strip() for t in self.topics.split(',')] if self.topics else [],
            'cover_filename': self.cover_filename,
            'cover_url': f"/static/covers/{self.cover_filename}" if self.cover_filename else None,
            'status': self.status,
            'is_favorite': self.is_favorite,
            'rating': self.rating,
            'added_at': self.added_at.strftime('%Y-%m-%d %H:%M')
        }

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="user") # 'master' ou 'user'
    verification_code = db.Column(db.String(6), nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_verified': self.is_verified,
            'is_master': self.role == 'master'
        }
