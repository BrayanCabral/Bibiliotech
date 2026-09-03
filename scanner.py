import os
import sys

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import re
import requests
import threading
from config import BOOKS_DIR, COVERS_DIR
from models import db, Book, Category

CATEGORY_ICONS = {
    "ALGORITMOS": ("Algoritmos & Estruturas de Dados", "cpu", "#f59e0b"),
    "ARQUITETURA": ("Arquitetura & Engenharia de Software", "layers", "#8b5cf6"),
    "BACK-END": ("Desenvolvimento Back-End", "database", "#10b981"),
    "FERRAMENTAS": ("DevOps & Ferramentas", "wrench", "#6366f1"),
    "FRONT-END": ("Desenvolvimento Front-End", "layout", "#ec4899"),
    "LOGICA DE PROGRAMAÇÃO": ("Lógica & Fundamentos", "code", "#3b82f6"),
    "GERAL": ("Engenharia & Geral", "book-open", "#14b8a6")
}

def clean_title_author(filename):
    """Limpa o nome do arquivo PDF para obter título e autor amigáveis."""
    name = os.path.splitext(filename)[0]
    name = re.sub(r'\(z-lib\.org\)', '', name, flags=re.IGNORECASE)
    name = re.sub(r'Casa do Codigo', '', name, flags=re.IGNORECASE)
    name = re.sub(r'Red Hat Developer', '', name, flags=re.IGNORECASE)
    name = re.sub(r'-', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()

    author = "Autor Desconhecido"

    if "Kevin Beaver" in filename:
        author = "Kevin Beaver"
    elif "Mary Provinciatto" in filename:
        author = "Mary Provinciatto"
    elif "Mauricio Aniche" in filename:
        author = "Maurício Aniche"
    elif "Robert C. Martin" in filename or "Código limpo" in filename:
        author = "Robert C. Martin (Uncle Bob)"
    elif "Pragmatic" in filename or "programador pragmatico" in filename.lower():
        author = "Andrew Hunt & David Thomas"
    elif "Cracking the Coding Interview" in filename or "CRACKING" in filename:
        author = "Gayle Laakmann McDowell"

    return name, author

def fetch_web_cover(title, book_id, app):
    """Busca a capa oficial do livro na internet em segundo plano."""
    clean_search = re.sub(r'[^\w\s]', '', title)
    try:
        url = f"https://www.googleapis.com/books/v1/volumes?q={requests.utils.quote(clean_search)}&maxResults=1"
        res = requests.get(url, timeout=3)
        if res.status_code == 200:
            data = res.json()
            items = data.get("items", [])
            if items:
                volume_info = items[0].get("volumeInfo", {})
                image_links = volume_info.get("imageLinks", {})
                thumbnail = image_links.get("thumbnail") or image_links.get("smallThumbnail")
                if thumbnail:
                    thumbnail = thumbnail.replace("http://", "https://")
                    img_res = requests.get(thumbnail, timeout=4)
                    if img_res.status_code == 200 and len(img_res.content) > 1000:
                        cover_filename = f"cover_{book_id}.jpg"
                        filepath = os.path.join(COVERS_DIR, cover_filename)
                        with open(filepath, "wb") as f:
                            f.write(img_res.content)
                        
                        # Atualizar livro no BD usando o app_context
                        with app.app_context():
                            b = Book.query.get(book_id)
                            if b:
                                b.cover_filename = cover_filename
                                db.session.commit()
                        print(f"Capa baixada com sucesso para: {title}")
    except Exception as e:
        print(f"Aviso ao buscar capa para {title}: {e}")

def generate_summary(title, category_name):
    """Gera um resumo/sinopse detalhado em português com tópicos principais."""
    title_lower = title.lower()
    
    if "código limpo" in title_lower or "clean code" in title_lower:
        summary = (
            "Mesmo um código ruim pode funcionar. Mas se ele não for limpo, pode acabar com uma empresa "
            "de desenvolvimento. Este livro é um marco na engenharia de software, apresentando boas práticas, "
            "refatoração, testes unitários e princípios SOLID para escrever códigos legíveis, elegantes e sustentáveis."
        )
        topics = "Clean Code, Refatoração, SOLID, Testes Unitários, Manutenibilidade"
    elif "cracking" in title_lower or "interview" in title_lower:
        summary = (
            "O guia definitivo de preparação para entrevistas técnicas nas maiores empresas de tecnologia do mundo. "
            "Contém mais de 180 perguntas e soluções sobre Estruturas de Dados, Algoritmos, Resolução de Problemas, "
            "Complexidade Big-O e Arquitetura de Sistemas."
        )
        topics = "Estruturas de Dados, Algoritmos, Big-O, Entrevistas Técnicas, Resolução de Problemas"
    elif "programador pragmático" in title_lower or "pragmatic" in title_lower:
        summary = (
            "Um dos livros de programação mais influentes de todos os tempos. Aborda desde a responsabilidade pessoal "
            "e o desenvolvimento de carreira até técnicas de codificação, ferramentas essenciais, refatoração "
            "e como evitar a podridão do software."
        )
        topics = "Carreira Dev, Boas Práticas, Automação, Arquitetura, Filosofia Pragmatic"
    elif "scrum" in title_lower or "sprint" in title_lower:
        summary = (
            "Guia prático sobre metodologias ágeis e a estrutura Scrum. Explica como gerenciar projetos com alta eficiência, "
            "entregas contínuas em sprints, papéis de Product Owner e Scrum Master, além de técnicas para maximizar o valor entregue."
        )
        topics = "Scrum, Agilidade, Sprints, Gestão de Projetos, Kanban"
    elif "segurança" in title_lower or "hacking" in title_lower:
        summary = (
            "Manual indispensável para compreender vulnerabilidades em aplicações web, testes de penetração (pentest), "
            "segurança de redes, proteção contra SQL Injection, XSS, CSRF e defesa cibernética ética."
        )
        topics = "Segurança Web, Hacking Ético, Vulnerabilidades, OWASP, Pentest"
    elif "react" in title_lower or "front" in title_lower or "js" in title_lower:
        summary = (
            "Manual completo para desenvolvimento de aplicações web e mobile modernas. Aborda componentes reutilizáveis, "
            "gerenciamento de estado, consumo de APIs REST, renderização reativa e boas práticas de UI/UX."
        )
        topics = "JavaScript, React, UI/UX, Front-End, Componentes"
    elif "python" in title_lower or "ruby" in title_lower or "go" in title_lower or "java" in title_lower or "c#" in title_lower:
        summary = (
            "Guia essencial da linguagem de programação. Cobre sintaxe avançada, orientação a objetos, "
            "tratamento de exceções, manipulação de dados, concorrência e construção de aplicações robustas."
        )
        topics = f"{category_name}, Sintaxe, Orientação a Objetos, Backend, APIs"
    else:
        summary = (
            f"Obra técnica focada em {category_name}. Apresenta conceitos fundamentais e avançados, "
            "exemplos práticos de código, padrões de projeto e diretrizes para desenvolvimento de aplicações de alta performance."
        )
        topics = f"{category_name}, Desenvolvimento de Software, Boas Práticas, Programação"

    return summary, topics

def scan_books_directory(app):
    """Escaneia a pasta C:\\Users\\braya\\Desktop\\Programming-Books e atualiza o banco de dados SQLite."""
    with app.app_context():
        if not os.path.exists(BOOKS_DIR):
            print(f"Diretório de livros não encontrado em {BOOKS_DIR}")
            return 0

        scanned_count = 0
        new_books_to_fetch = []

        for root, dirs, files in os.walk(BOOKS_DIR):
            for file in files:
                if file.lower().endswith('.pdf'):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(root, BOOKS_DIR)

                    top_folder = rel_path.split(os.sep)[0].upper() if rel_path != '.' else "GERAL"
                    cat_info = CATEGORY_ICONS.get(top_folder, ("Engenharia & Geral", "book-open", "#14b8a6"))
                    
                    category = Category.query.filter_by(name=cat_info[0]).first()
                    if not category:
                        slug = re.sub(r'\W+', '-', cat_info[0].lower()).strip('-')
                        category = Category(
                            name=cat_info[0],
                            slug=slug,
                            icon=cat_info[1],
                            color=cat_info[2]
                        )
                        db.session.add(category)
                        db.session.commit()

                    book = Book.query.filter_by(file_path=full_path).first()
                    file_size_mb = os.path.getsize(full_path) / (1024 * 1024)
                    title, author = clean_title_author(file)
                    summary, topics = generate_summary(title, category.name)

                    if not book:
                        book = Book(
                            title=title,
                            original_filename=file,
                            file_path=full_path,
                            file_size_mb=file_size_mb,
                            file_format="PDF",
                            category_id=category.id,
                            category_name=category.name,
                            author=author,
                            summary=summary,
                            topics=topics,
                            status="Quero Ler",
                            is_favorite=False
                        )
                        db.session.add(book)
                        db.session.commit()
                        scanned_count += 1
                        new_books_to_fetch.append((book.title, book.id))
                    elif not book.cover_filename:
                        new_books_to_fetch.append((book.title, book.id))

        # Iniciar busca de capas em thread separada para não travar a inicialização
        if new_books_to_fetch:
            def background_fetch():
                for t, b_id in new_books_to_fetch:
                    fetch_web_cover(t, b_id, app)

            t = threading.Thread(target=background_fetch, daemon=True)
            t.start()

        print(f"Escaneamento rápido concluído. {scanned_count} novos livros catalogados.")
        return scanned_count

