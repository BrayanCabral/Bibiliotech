# 📚 BiblioTech

> Biblioteca digital em Flask com catalogação automática de PDFs, leitor embutido e um
> assistente de IA local que recomenda livros do acervo — com o retrieval por palavras-chave
> implementado à mão, sem framework de RAG.

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Ollama](https://img.shields.io/badge/Ollama-local%20LLM-000000)](https://ollama.com/)
[![Render](https://img.shields.io/badge/deploy-Render-46E3B7)](https://render.com/)

*[English version below](#-english)*

---

## O problema

Acervos digitais de PDFs viram pastas mortas. Os arquivos existem, mas ninguém sabe o que
há dentro: o nome do arquivo não diz o assunto, não há busca por tema e não há como saber
em que página você parou.

O BiblioTech transforma uma pasta de PDFs em uma biblioteca navegável — catalogada
automaticamente, pesquisável por tema e com um assistente que entende o que você procura
mesmo sem saber o título.

## O foco do projeto: direcionar a resposta da IA por palavras-chave

O objetivo central não era plugar um chatbot. Era estudar **como conduzir a resposta de um
modelo de linguagem através de recuperação por palavras-chave** — o problema clássico de
RAG, resolvido sem framework, para entender o mecanismo por dentro.

O pipeline em `chatbot.py`:

1. **Extração de palavras-chave** — a mensagem é normalizada, tokenizada em termos de 3+
   caracteres e filtrada por uma lista de ~40 *stopwords* em português montada para o
   domínio. Palavras como "livro", "quero" e "recomendar" são ruído aqui, não sinal.
2. **Pontuação de relevância** — cada livro recebe um score pela ocorrência dos termos em
   título, autor, categoria, tópicos e resumo. Só entra quem pontua acima de zero.
3. **Corte de candidatos** — no máximo 20 livros, ordenados por relevância. Sem esse corte,
   o acervo inteiro estouraria a janela de contexto e diluiria a resposta.
4. **Montagem do contexto** — os candidatos são serializados como
   `título | autor | categoria | tópicos | status` e injetados no system prompt, junto com o
   histórico da conversa.
5. **Chamada ao modelo** — POST para o Ollama, com tratamento de erro de conexão e timeout.

O aprendizado prático: **a qualidade da resposta depende muito mais da etapa de recuperação
do que do modelo.** Filtrar bem os candidatos antes do prompt teve mais efeito do que trocar
o modelo — e é o que impede o assistente de recomendar livros que não existem no acervo.

O modelo roda localmente via Ollama: sem chave de API, sem custo por requisição e sem dado
saindo da máquina.

## Funcionalidades

- **Catalogação automática** — o scanner varre o diretório de PDFs, extrai metadados com
  `pypdf`, infere título, autor, categoria e tópicos, gera a capa a partir da primeira página
  e popula o banco. Sem cadastro manual.
- **Leitor no navegador** — leitura direta na aplicação, sem download.
- **Arquimedes** — o assistente descrito acima, em LLM local.
- **Autenticação** — login por usuário ou e-mail, senhas com hash, papéis `master` e `user`.
- **Organização** — categorias, favoritos, avaliação, status de leitura e estatísticas.

## Stack

| Camada | Tecnologia |
|---|---|
| Back-end | Python 3.11 · Flask 3.0.3 · Flask-SQLAlchemy 3.1.1 |
| Banco | PostgreSQL (`psycopg2-binary`) |
| Front-end | HTML · CSS · JavaScript |
| LLM | Ollama — `gemma4:12b` (configurável) |
| PDFs | pypdf 4.2.0 |
| Servidor | Gunicorn 22 |
| Deploy | Render (`render.yaml` · `Procfile` · `runtime.txt`) |

## Como rodar

**Pré-requisitos:** Python 3.11, PostgreSQL e [Ollama](https://ollama.com/) instalados.

```bash
git clone https://github.com/BrayanCabral/Bibliotech.git
cd Bibliotech

python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux/macOS

pip install -r requirements.txt
```

Baixe o modelo uma única vez (alguns GB):

```bash
ollama pull gemma4:12b
```

Configure o ambiente:

```bash
cp .env.example .env
```

| Variável | Obrigatória | Descrição |
|---|---|---|
| `SECRET_KEY` | sim | Chave de sessão do Flask |
| `DATABASE_URL` | sim | String de conexão do PostgreSQL |
| `MASTER_PASSWORD` | não | Fixa a senha do usuário master; sem ela, uma senha aleatória é gerada e exibida no console |
| `OLLAMA_BASE_URL` | não | Padrão `http://localhost:11434` |
| `OLLAMA_MODEL` | não | Padrão `gemma4:12b` |

Suba a aplicação:

```bash
python app.py
```

Acesse `http://localhost:5000`. Coloque seus PDFs no diretório do acervo e dispare a
varredura pela interface.

> Os PDFs não fazem parte deste repositório — são ignorados por `.gitignore`.

## Decisões técnicas

**Retrieval próprio em vez de biblioteca de RAG.** O objetivo era entender o mecanismo, não
abstraí-lo. Implementar extração de termos, scoring e corte de candidatos na mão deixou claro
onde a qualidade da resposta realmente se decide.

**LLM local em vez de API.** Sem chave, sem custo por requisição, sem dado do acervo saindo
da máquina — e o projeto roda para qualquer pessoa que o clone.

**Catalogação automática em vez de cadastro manual.** A barreira de qualquer biblioteca
digital é alimentar o catálogo; extrair metadados direto do PDF elimina esse atrito.

**Configuração externalizada.** Nenhum valor sensível no código: tudo por variável de
ambiente, com `.env.example` como referência.

## Roadmap

- [ ] Embeddings e busca vetorial, para comparar com o retrieval por palavras-chave
- [ ] Busca full-text no conteúdo dos PDFs
- [ ] Recomendação por histórico de leitura
- [ ] Testes automatizados e CI
- [ ] Suporte a EPUB

## Autor

**Brayan Cabral** — Analista de Sistemas | Back-end Developer

[![LinkedIn](https://img.shields.io/badge/LinkedIn-brayancabral-0A66C2?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/brayancabral/)

---

## 🇺🇸 English

**BiblioTech** turns a folder of PDFs into a searchable digital library: automatic
cataloging, an in-browser reader, and a locally-run AI assistant that recommends titles
from the collection.

The heart of the project is a study in **steering an LLM's answers through keyword-based
retrieval** — the classic RAG problem, solved without a framework in order to understand
the mechanism. The pipeline extracts keywords from the user's message (filtered through a
domain-specific Portuguese stopword list), scores every book by term occurrence across
title, author, category, topics and summary, caps the candidate set at 20 to protect the
context window, and only then builds the system prompt. The practical takeaway: answer
quality depends far more on the retrieval step than on the model — and good filtering is
what stops the assistant from recommending books the library doesn't have.

The model runs locally through Ollama: no API key, no per-request cost, no data leaving
the machine.

**Stack:** Python 3.11 · Flask 3.0.3 · SQLAlchemy · PostgreSQL · pypdf · Ollama · Gunicorn · Render.

```bash
git clone https://github.com/BrayanCabral/Bibliotech.git
cd Bibliotech
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
ollama pull gemma4:12b
cp .env.example .env      # set SECRET_KEY and DATABASE_URL
python app.py
```

**Roadmap:** vector search with embeddings (to benchmark against keyword retrieval) ·
full-text PDF search · history-based recommendations · automated tests and CI · EPUB.

---

<sub>Projeto pessoal de estudo. O acervo de PDFs não faz parte deste repositório.</sub>
