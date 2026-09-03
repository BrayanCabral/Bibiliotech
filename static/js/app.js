// ============================================================
// Estado Global
// ============================================================
const state = {
    categoryId: '',
    search: '',
    favorites: false,
    sort: 'title',
    books: [],
    categories: [],
    currentUser: null
};

let pendingVerifyEmail = '';

// ============================================================
// Inicialização
// ============================================================
document.addEventListener('DOMContentLoaded', async () => {
    feather.replace();
    await checkAuth();
});

// ============================================================
// Autenticação
// ============================================================
async function checkAuth() {
    try {
        const res = await fetch('/api/auth/me');
        const data = await res.json();
        state.currentUser = data.logged_in ? data.user : null;
    } catch {
        state.currentUser = null;
    }
    // O dashboard é exibido sempre. O login é opcional e só é pedido
    // quando uma ação específica exigir um usuário identificado.
    showApp();
}

// Abre o login/cadastro como uma janela opcional por cima do dashboard
function showAuthWall() {
    document.getElementById('authWall').classList.add('open');
    feather.replace();
}

// Fecha a janela de login sem sair do dashboard (navegação anônima)
function closeAuthWall() {
    document.getElementById('authWall').classList.remove('open');
}

function showApp() {
    closeAuthWall();
    document.getElementById('appMain').style.display = 'block';

    // Badge e botões de sessão
    const badge = document.getElementById('userBadge');
    const btnLogout = document.getElementById('btnLogout');
    const btnLoginNav = document.getElementById('btnLoginNav');

    if (state.currentUser) {
        badge.textContent = state.currentUser.role === 'master'
            ? `MASTER: ${state.currentUser.username}`
            : state.currentUser.username;
        badge.style.display = state.currentUser.role === 'master' ? 'inline-flex' : 'none';
        btnLogout.style.display = 'inline-flex';
        btnLoginNav.style.display = 'none';
    } else {
        badge.style.display = 'none';
        btnLogout.style.display = 'none';
        btnLoginNav.style.display = 'inline-flex';
    }

    feather.replace();
    initApp();
}

// Exige um usuário logado para executar uma ação; se anônimo, abre o login
// e devolve false para o chamador cancelar a ação.
function requireAuth() {
    if (!state.currentUser) {
        showAuthWall();
        return false;
    }
    return true;
}

function showTab(tab) {
    document.getElementById('loginForm').style.display = tab === 'login' ? 'flex' : 'none';
    document.getElementById('registerForm').style.display = tab === 'register' ? 'flex' : 'none';
    document.getElementById('verifyForm').style.display = 'none';
    document.getElementById('tabLogin').classList.toggle('active', tab === 'login');
    document.getElementById('tabRegister').classList.toggle('active', tab === 'register');
}

async function handleLogin(e) {
    e.preventDefault();
    const errEl = document.getElementById('loginError');
    errEl.style.display = 'none';

    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value;

    try {
        const res = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await res.json();

        if (data.success) {
            state.currentUser = data.user;
            showApp();
        } else if (data.needs_verification) {
            pendingVerifyEmail = data.email;
            showVerifyForm(data.email);
        } else {
            errEl.textContent = data.error || 'Erro ao fazer login.';
            errEl.style.display = 'block';
        }
    } catch {
        errEl.textContent = 'Erro de conexão.';
        errEl.style.display = 'block';
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const errEl = document.getElementById('registerError');
    errEl.style.display = 'none';

    const username = document.getElementById('regUsername').value.trim();
    const email = document.getElementById('regEmail').value.trim();
    const password = document.getElementById('regPassword').value;

    try {
        const res = await fetch('/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password })
        });
        const data = await res.json();

        if (data.success) {
            pendingVerifyEmail = data.email;
            showVerifyForm(data.email);
        } else {
            errEl.textContent = data.error || 'Erro ao cadastrar.';
            errEl.style.display = 'block';
        }
    } catch {
        errEl.textContent = 'Erro de conexão.';
        errEl.style.display = 'block';
    }
}

function showVerifyForm(email) {
    document.getElementById('loginForm').style.display = 'none';
    document.getElementById('registerForm').style.display = 'none';
    document.getElementById('verifyForm').style.display = 'flex';
    document.getElementById('verifyEmailLabel').textContent = email;
    document.getElementById('tabLogin').classList.remove('active');
    document.getElementById('tabRegister').classList.remove('active');
    feather.replace();
}

async function handleVerify(e) {
    e.preventDefault();
    const errEl = document.getElementById('verifyError');
    errEl.style.display = 'none';

    const code = document.getElementById('verifyCode').value.trim();

    try {
        const res = await fetch('/api/auth/verify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: pendingVerifyEmail, code })
        });
        const data = await res.json();

        if (data.success) {
            state.currentUser = data.user;
            showApp();
        } else {
            errEl.textContent = data.error || 'Código inválido.';
            errEl.style.display = 'block';
        }
    } catch {
        errEl.textContent = 'Erro de conexão.';
        errEl.style.display = 'block';
    }
}

async function handleLogout() {
    await fetch('/api/auth/logout', { method: 'POST' });
    state.currentUser = null;
    showApp(); // continua no dashboard, agora em modo anônimo
}

// ============================================================
// App Principal
// ============================================================
let listenersInitialized = false;

function initApp() {
    if (!listenersInitialized) {
        setupEventListeners();
        listenersInitialized = true;
    }
    loadStats();
    loadCategories();
    loadBooks();
}

function setupEventListeners() {
    // Busca com debounce
    let searchTimeout;
    const searchInput = document.getElementById('searchInput');
    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            state.search = e.target.value;
            loadBooks();
        }, 300);
    });

    // Ordenação
    document.getElementById('sortSelect').addEventListener('change', (e) => {
        state.sort = e.target.value;
        loadBooks();
    });

    // Favoritos
    document.getElementById('btnFavoritesFilter').addEventListener('click', () => {
        state.favorites = !state.favorites;
        document.getElementById('btnFavoritesFilter').classList.toggle('active', state.favorites);
        loadBooks();
    });

    // Escanear
    document.getElementById('btnScan').addEventListener('click', async () => {
        if (!requireAuth()) return;
        const btn = document.getElementById('btnScan');
        btn.disabled = true;
        btn.innerHTML = `<i data-feather="loader"></i>`;
        feather.replace();

        try {
            const res = await fetch('/api/scan', { method: 'POST' });
            const data = await res.json();
            alert(`Escaneamento concluído! ${data.new_books_count} novos livros.`);
            await loadStats();
            await loadCategories();
            await loadBooks();
        } catch {
            alert('Erro ao escanear.');
        } finally {
            btn.disabled = false;
            btn.innerHTML = `<i data-feather="refresh-cw"></i> <span class="btn-label">Escanear</span>`;
            feather.replace();
        }
    });

    // Fechar modais
    document.getElementById('btnCloseSummary').addEventListener('click', () => {
        document.getElementById('summaryModal').classList.remove('open');
    });

    document.getElementById('btnCloseReader').addEventListener('click', () => {
        document.getElementById('readerModal').classList.remove('open');
        // Bug fix: limpar o iframe completamente ao fechar
        const frame = document.getElementById('pdfFrame');
        frame.src = 'about:blank';
    });

    // Fechar menu mobile ao clicar fora
    document.getElementById('mobileCategoryMenu').addEventListener('click', (e) => {
        if (e.target === e.currentTarget) toggleCategoryMenu();
    });

    // Fechar janela de login sem logar (navegação anônima continua)
    document.getElementById('btnCloseAuthWall').addEventListener('click', closeAuthWall);
    document.getElementById('authWall').addEventListener('click', (e) => {
        if (e.target === e.currentTarget) closeAuthWall();
    });
}

// ============================================================
// Menu Mobile de Categorias
// ============================================================
function toggleCategoryMenu() {
    const menu = document.getElementById('mobileCategoryMenu');
    menu.classList.toggle('open');
    feather.replace();
}

function buildMobileCategoryMenu() {
    const list = document.getElementById('mobileCatList');
    list.innerHTML = `
        <div class="mobile-cat-item ${state.categoryId === '' ? 'active' : ''}" onclick="selectMobileCategory('')">
            <i data-feather="book"></i> Todos os Livros
        </div>
        ${state.categories.map(c => `
            <div class="mobile-cat-item ${state.categoryId == c.id ? 'active' : ''}"
                 onclick="selectMobileCategory('${c.id}')">
                <i data-feather="${c.icon || 'folder'}"></i> ${c.name} (${c.book_count})
            </div>
        `).join('')}
    `;
    feather.replace();
}

function selectMobileCategory(catId) {
    state.categoryId = catId;
    toggleCategoryMenu();
    syncDesktopCategoryPills();
    loadBooks();
}

function syncDesktopCategoryPills() {
    document.querySelectorAll('.cat-pill').forEach(p => {
        p.classList.toggle('active', p.dataset.category == state.categoryId);
    });
}

// ============================================================
// Carregar Estatísticas
// ============================================================
async function loadStats() {
    try {
        const res = await fetch('/api/stats');
        const stats = await res.json();

        document.getElementById('statTotalBooks').textContent = stats.total_books;
        document.getElementById('statReadBooks').textContent = stats.read_books;
        document.getElementById('statCategories').textContent = stats.total_categories;

        // Espaço em disco: apenas para master
        const diskCard = document.getElementById('statDiskCard');
        if (stats.is_master && stats.total_gb !== undefined) {
            document.getElementById('statTotalGB').textContent = `${stats.total_gb} GB`;
            diskCard.style.display = 'flex';
        } else {
            diskCard.style.display = 'none';
        }
    } catch (err) {
        console.error('Erro ao carregar estatísticas:', err);
    }
}

// ============================================================
// Carregar Categorias
// ============================================================
async function loadCategories() {
    try {
        const res = await fetch('/api/categories');
        state.categories = await res.json();

        const container = document.getElementById('categoriesContainer');
        container.innerHTML = `
            <button class="cat-pill ${state.categoryId === '' ? 'active' : ''}" data-category="">Todos os Livros</button>
            ${state.categories.map(c => `
                <button class="cat-pill ${state.categoryId == c.id ? 'active' : ''}" data-category="${c.id}">
                    ${c.name} (${c.book_count})
                </button>
            `).join('')}
        `;

        container.querySelectorAll('.cat-pill').forEach(pill => {
            pill.addEventListener('click', () => {
                state.categoryId = pill.dataset.category;
                syncDesktopCategoryPills();
                buildMobileCategoryMenu();
                loadBooks();
            });
        });

        buildMobileCategoryMenu();
    } catch (err) {
        console.error('Erro ao carregar categorias:', err);
    }
}

// ============================================================
// Carregar Livros
// ============================================================
async function loadBooks() {
    try {
        const params = new URLSearchParams({
            category_id: state.categoryId,
            search: state.search,
            favorites: state.favorites,
            sort: state.sort
        });

        const res = await fetch(`/api/books?${params}`);
        state.books = await res.json();
        renderBooks();
    } catch (err) {
        console.error('Erro ao carregar livros:', err);
    }
}

// ============================================================
// Renderizar Cards de Livros
// ============================================================
function renderBooks() {
    const grid = document.getElementById('booksGrid');
    document.getElementById('booksCount').textContent = `${state.books.length} obras`;

    if (state.books.length === 0) {
        grid.innerHTML = `
            <div style="grid-column:1/-1;text-align:center;padding:60px 20px;color:var(--text-muted);">
                <i data-feather="book-open" style="width:48px;height:48px;margin-bottom:10px;"></i>
                <p>Nenhum livro encontrado.</p>
            </div>`;
        feather.replace();
        return;
    }

    grid.innerHTML = state.books.map(book => {
        const statusClass = 'status-' + book.status.replace(/ /g, '-');
        return `
        <div class="book-card" data-id="${book.id}">
            <div class="book-cover-container">
                ${book.cover_url
                    ? `<img src="${book.cover_url}" alt="${book.title}" class="book-cover-img"
                           onerror="this.style.display='none';this.nextElementSibling.style.display='flex';">
                       <div class="fallback-cover" style="display:none;">
                           <i data-feather="book"></i><h4>${book.title}</h4>
                       </div>`
                    : `<div class="fallback-cover">
                           <i data-feather="book"></i><h4>${book.title}</h4>
                       </div>`
                }
                <button class="btn-favorite ${book.is_favorite ? 'active' : ''}" data-id="${book.id}">
                    <i data-feather="heart" ${book.is_favorite ? 'style="fill:var(--accent-pink);"' : ''}></i>
                </button>
            </div>
            <div class="book-details">
                <div class="book-meta">
                    <span class="category-tag" title="${book.category_name}">${book.category_name}</span>
                    <span class="status-badge ${statusClass}">${book.status}</span>
                </div>
                <h3 class="book-title" title="${book.title}">${book.title}</h3>
                <p class="book-author">${book.author}</p>
                <p style="font-size:0.75rem;color:var(--text-muted);">${book.file_size_mb} MB • ${book.file_format}</p>
                <div class="book-actions">
                    <button class="btn btn-secondary btn-sm btn-summary" data-id="${book.id}">
                        <i data-feather="info"></i> Resumo
                    </button>
                    <button class="btn btn-primary btn-sm btn-read" data-id="${book.id}" data-title="${book.title}">
                        <i data-feather="eye"></i> Ler PDF
                    </button>
                </div>
            </div>
        </div>`;
    }).join('');

    feather.replace();

    // Bind favoritos
    grid.querySelectorAll('.btn-favorite').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            if (!requireAuth()) return;
            const book = state.books.find(b => b.id == btn.dataset.id);
            if (book) {
                book.is_favorite = !book.is_favorite;
                await updateBook(book.id, { is_favorite: book.is_favorite });
                renderBooks();
                loadStats();
            }
        });
    });

    // Bind resumo
    grid.querySelectorAll('.btn-summary').forEach(btn => {
        btn.addEventListener('click', () => openSummaryModal(btn.dataset.id));
    });

    // Bind ler PDF
    grid.querySelectorAll('.btn-read').forEach(btn => {
        btn.addEventListener('click', () => openReaderModal(btn.dataset.id, btn.dataset.title));
    });
}

// ============================================================
// Modal de Resumo
// ============================================================
async function openSummaryModal(bookId) {
    try {
        const res = await fetch(`/api/books/${bookId}`);
        const book = await res.json();
        const statusClass = 'status-' + book.status.replace(/ /g, '-');

        document.getElementById('modalSummaryBody').innerHTML = `
            <div class="summary-content">
                <div class="summary-cover">
                    ${book.cover_url
                        ? `<img src="${book.cover_url}" alt="${book.title}">`
                        : `<div class="fallback-cover" style="height:280px;">
                               <i data-feather="book" style="width:48px;height:48px;"></i>
                               <h3>${book.title}</h3>
                           </div>`
                    }
                </div>
                <div class="summary-details">
                    <h2>${book.title}</h2>
                    <p class="summary-author">por ${book.author}</p>
                    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px;">
                        <span class="category-tag">${book.category_name}</span>
                        <span class="status-badge ${statusClass}">${book.status}</span>
                        <span style="font-size:0.8rem;color:var(--text-muted);padding-top:2px;">${book.file_size_mb} MB</span>
                    </div>
                    <h4 style="font-family:'Outfit';margin-bottom:8px;">Sinopse:</h4>
                    <div class="summary-box"><p>${book.summary || 'Resumo não disponível.'}</p></div>
                    <h4 style="font-family:'Outfit';margin-bottom:8px;">Tópicos & Tecnologias:</h4>
                    <div class="topics-tags">
                        ${book.topics.map(t => `<span class="topic-tag">${t}</span>`).join('')}
                    </div>
                    <div style="display:flex;gap:12px;margin-top:20px;flex-wrap:wrap;">
                        <button class="btn btn-primary" id="btnModalRead" data-id="${book.id}" data-title="${book.title}">
                            <i data-feather="book-open"></i> Ler Agora
                        </button>
                        <select id="modalStatus" style="background:rgba(30,41,59,0.9);border:1px solid var(--border-color);color:#fff;padding:10px 14px;border-radius:var(--radius-md);outline:none;">
                            <option value="Quero Ler" ${book.status === 'Quero Ler' ? 'selected' : ''}>Quero Ler</option>
                            <option value="Lendo" ${book.status === 'Lendo' ? 'selected' : ''}>Lendo</option>
                            <option value="Lido" ${book.status === 'Lido' ? 'selected' : ''}>Lido</option>
                        </select>
                    </div>
                </div>
            </div>`;

        feather.replace();
        document.getElementById('summaryModal').classList.add('open');

        document.getElementById('btnModalRead').addEventListener('click', () => {
            document.getElementById('summaryModal').classList.remove('open');
            openReaderModal(book.id, book.title);
        });

        document.getElementById('modalStatus').addEventListener('change', async (e) => {
            if (!requireAuth()) {
                e.target.value = book.status; // reverte a seleção
                return;
            }
            await updateBook(book.id, { status: e.target.value });
            loadStats();
            loadBooks();
        });
    } catch (err) {
        console.error('Erro ao abrir resumo:', err);
    }
}

// ============================================================
// Leitor de PDF - BUGFIX: sempre inicia na página 1
// ============================================================
function openReaderModal(bookId, bookTitle) {
    const frame = document.getElementById('pdfFrame');
    const modal = document.getElementById('readerModal');

    // Limpar iframe primeiro para resetar completamente
    frame.src = 'about:blank';

    document.getElementById('readerBookTitle').textContent = bookTitle;

    // Pequeno delay para garantir o reset antes de carregar o novo PDF
    setTimeout(() => {
        // #page=1 força o visualizador do navegador a iniciar na primeira página
        frame.src = `/api/books/${bookId}/pdf#page=1`;
    }, 50);

    modal.classList.add('open');
}

// ============================================================
// Atualizar Livro no Servidor
// ============================================================
async function updateBook(bookId, payload) {
    try {
        await fetch(`/api/books/${bookId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
    } catch (err) {
        console.error('Erro ao atualizar livro:', err);
    }
}

// ============================================================
// Chatbot Arquimedes
// ============================================================
const arquimedesState = {
    history: [],
    opened: false
};

document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.getElementById('btnArquimedesToggle');
    const closeBtn = document.getElementById('btnCloseArquimedes');
    const form = document.getElementById('arquimedesForm');

    toggleBtn.addEventListener('click', toggleArquimedesChat);
    closeBtn.addEventListener('click', () => {
        document.getElementById('arquimedesChat').classList.remove('open');
    });
    form.addEventListener('submit', handleArquimedesSubmit);
});

function toggleArquimedesChat() {
    const chat = document.getElementById('arquimedesChat');
    const isOpen = chat.classList.toggle('open');

    if (isOpen && !arquimedesState.opened) {
        arquimedesState.opened = true;
        addArquimedesMessage('assistant',
            'Olá! Eu sou o Arquimedes 📚 Me conte o que você quer aprender ou qual tecnologia te interessa, que eu recomendo um livro do acervo para você.');
    }
    if (isOpen) {
        feather.replace();
        document.getElementById('arquimedesInput').focus();
    }
}

function addArquimedesMessage(role, text) {
    const container = document.getElementById('arquimedesMessages');
    const bubble = document.createElement('div');
    bubble.className = `arq-msg ${role}`;
    bubble.textContent = text;
    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
    return bubble;
}

async function handleArquimedesSubmit(e) {
    e.preventDefault();
    const input = document.getElementById('arquimedesInput');
    const sendBtn = document.getElementById('btnArquimedesSend');
    const message = input.value.trim();
    if (!message) return;

    addArquimedesMessage('user', message);
    input.value = '';
    input.disabled = true;
    sendBtn.disabled = true;

    const loadingBubble = addArquimedesMessage('loading', 'Arquimedes está pensando...');

    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, history: arquimedesState.history })
        });
        const data = await res.json();

        loadingBubble.remove();

        const reply = data.reply || data.error || 'Não consegui responder agora.';
        addArquimedesMessage('assistant', reply);

        arquimedesState.history.push({ role: 'user', content: message });
        arquimedesState.history.push({ role: 'assistant', content: reply });
    } catch (err) {
        loadingBubble.remove();
        addArquimedesMessage('assistant', 'Erro de conexão ao falar com o Arquimedes.');
        console.error('Erro no chat Arquimedes:', err);
    } finally {
        input.disabled = false;
        sendBtn.disabled = false;
        input.focus();
    }
}
