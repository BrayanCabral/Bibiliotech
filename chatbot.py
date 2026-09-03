import os
import re
import sys

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import requests

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_URL = f"{OLLAMA_BASE_URL}/api/chat"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma4:12b")
MAX_CANDIDATE_BOOKS = 20

STOPWORDS = {
    "que", "para", "com", "uma", "um", "das", "dos", "sobre", "quero", "queria",
    "aprender", "gostaria", "gostar", "voce", "você", "tem", "tenho", "algum",
    "alguma", "bom", "boa", "livro", "livros", "indicar", "indica", "recomendar",
    "recomenda", "recomendação", "recomendacao", "qual", "quais", "pode", "poderia",
    "estou", "sou", "meu", "minha", "saber", "mais", "isso", "esse", "essa", "aquele",
    "aquela", "onde", "como", "porque", "por", "sao", "são", "seria", "ser", "estar"
}


def extract_keywords(message):
    words = re.findall(r"\w+", message.lower())
    return [w for w in words if len(w) >= 3 and w not in STOPWORDS]


def filter_relevant_books(message, books, limit=MAX_CANDIDATE_BOOKS):
    keywords = extract_keywords(message)
    if not keywords:
        return books[:limit]

    scored = []
    for b in books:
        haystack = f"{b.title} {b.author} {b.category_name} {b.topics or ''} {b.summary or ''}".lower()
        score = sum(1 for kw in keywords if kw in haystack)
        if score > 0:
            scored.append((score, b))

    if not scored:
        return books[:limit]

    scored.sort(key=lambda x: x[0], reverse=True)
    return [b for _, b in scored[:limit]]


SYSTEM_PROMPT_TEMPLATE = """Você é Arquimedes, o assistente de leitura da biblioteca BiblioTech.
Seu único papel é ajudar o usuário a escolher qual livro do acervo ler a seguir.

Regras importantes:
- Recomende exclusivamente livros que aparecem na lista abaixo. Nunca invente ou sugira livros que não estejam nela.
- Sempre cite o título exato do livro (como aparece na lista) ao recomendar.
- A lista abaixo é uma seleção relevante do acervo (não é a biblioteca inteira), filtrada com base na pergunta do usuário.
- Considere o interesse do usuário, os tópicos/tecnologias dos livros e, quando fizer sentido, o status de leitura (não recomende algo que ele já marcou como "Lido", a menos que ele peça releitura).
- Se a lista abaixo não tiver nada adequado, diga isso claramente ao usuário, sem inventar títulos.
- Seja objetivo, simpático, direto ao ponto, e responda em português do Brasil.

Livros relevantes encontrados no acervo (título | autor | categoria | tópicos | status):
{catalog}
"""


def build_catalog_context(books):
    lines = []
    for b in books:
        topics = b.topics or ""
        lines.append(f"- {b.title} | {b.author} | {b.category_name} | {topics} | {b.status}")
    return "\n".join(lines) if lines else "(nenhum livro correspondente encontrado)"


def ask_arquimedes(message, history, books):
    candidates = filter_relevant_books(message, books)
    catalog = build_catalog_context(candidates)
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(catalog=catalog)

    messages = [{"role": "system", "content": system_prompt}]
    for h in history:
        role = h.get("role")
        content = h.get("content")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": message})

    try:
        res = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "messages": messages, "stream": False, "think": False},
            timeout=90
        )
        res.raise_for_status()
        data = res.json()
        return data.get("message", {}).get("content", "Desculpe, não consegui gerar uma resposta.")
    except requests.exceptions.ConnectionError:
        return "Não consegui me conectar ao Ollama local. Verifique se o serviço está rodando em localhost:11434."
    except requests.exceptions.ReadTimeout:
        return "O Arquimedes demorou demais para responder (modelo local lento). Tente uma pergunta mais direta ou aguarde e tente novamente."
    except Exception as e:
        return f"Ocorreu um erro ao consultar o Arquimedes: {e}"
