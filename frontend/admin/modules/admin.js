// modules/admin.js
import { API_URL, checkAuth, fetchProtected } from './core.js';

const ITEMS_PER_PAGE = 5; 

// Редактор Quill (для вкладки Новини, ініціалізуємо в DOMContentLoaded)
let quill = null;

// --- ІНІЦІАЛІЗАЦІЯ ЛОГІНУ (БЕЗ ПЕРЕЗАВАНТАЖЕННЯ СТОРІНКИ) ---
document.addEventListener('DOMContentLoaded', () => {
    // Ініціалізуємо Quill коли DOM готовий
    const quillEditor = document.querySelector('#quill-editor');
    if (quillEditor && typeof Quill !== 'undefined') {
        quill = new Quill('#quill-editor', {
            theme: 'snow',
            placeholder: 'Напишіть вашу статтю тут...',
            modules: { toolbar: [ [{ 'header': [2, 3, false] }], ['bold', 'italic', 'underline'], [{ 'list': 'ordered'}, { 'list': 'bullet' }], ['link'], ['clean'] ] }
        });
    }

    if (checkAuth()) {
        window.loadInitialData();
    }

    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const u = document.getElementById('username').value;
            const p = document.getElementById('password').value;
            const err = document.getElementById('login-error');
            const btn = loginForm.querySelector('button');
            
            btn.textContent = 'Перевірка...';
            err.style.display = 'none';

            try {
                const res = await fetch(`${API_URL}/login`, { 
                    method: 'POST', 
                    headers: { 'Content-Type': 'application/json' }, 
                    body: JSON.stringify({ username: u, password: p }) 
                });
                
                if (res.ok) {
                    const data = await res.json();
                    localStorage.setItem('bti_token', data.access_token);
                    checkAuth(); // Миттєво перемикаємо на адмінку
                    window.loadInitialData(); // Вантажимо дані
                } else {
                    err.style.display = 'block';
                }
            } catch(error) {
                err.style.display = 'block';
                err.textContent = 'Помилка з\'єднання з сервером';
            } finally {
                btn.textContent = 'Увійти';
            }
        });
    }

    // Инициализируем обработчики форм
    initFormHandlers();
});

// Функция инициализации всех обработчиков форм
function initFormHandlers() {
    // FAQ-форма
    const faqForm = document.getElementById('faq-form');
    if (faqForm) {
        faqForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const q = document.getElementById('faq-question').value;
            const a = document.getElementById('faq-answer').value;
            if (!q || !a) {
                window.showStatus('Заповніть обидва поля', true);
                return;
            }
            try {
                await fetchProtected(`${API_URL}/faqs`, { method: 'POST', body: JSON.stringify({ question: q, answer: a }) });
                document.getElementById('faq-question').value = '';
                document.getElementById('faq-answer').value = '';
                window.showStatus('Питання додано!');
                window.loadFaqs();
            } catch(e) { console.error('Помилка додавання FAQ:', e); window.showStatus('Помилка при додаванні питання', true); }
        });
    }

    // Services-форма
    const servicesForm = document.getElementById('services-form');
    if (servicesForm) {
        servicesForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const select = document.getElementById('service-slug-select');
            const slug = select.value;
            const title = document.getElementById('service-title').value;
            const raw = document.getElementById('service-table-raw').value;
            const table_data = raw.split('\n').filter(Boolean).map(line => line.split(';').map(s => s.trim()));
            try {
                await fetchProtected(`${API_URL}/services/${slug}`, { method: 'POST', body: JSON.stringify({ title, table_data }) });
                window.showStatus('Послугу збережено!');
            } catch(e) { console.error('Помилка збереження послуги:', e); window.showStatus('Помилка при збереженні послуги', true); }
        });
    }

    // News-форма
    const newsForm = document.getElementById('news-form');
    if (newsForm) {
        newsForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const id = document.getElementById('news-id').value;
            const title = document.getElementById('news-title').value;
            const date_str = document.getElementById('news-date').value;
            const tag = document.getElementById('news-tag').value;
            const preview = document.getElementById('news-preview').value;
            const bodyHtml = quill ? quill.root.innerHTML : '';

            let image_url = '';
            const fileInput = document.getElementById('news-image');
            const file = fileInput?.files[0];
            if (file) {
                try {
                    image_url = await window.uploadImageFile(file);
                } catch(e) {
                    window.showStatus('Не вдалося завантажити зображення', true);
                    return;
                }
            }

            const payload = { title, date_str, tag, image_url, preview, content: bodyHtml };
            const method = id ? 'PUT' : 'POST';
            const url = id ? `${API_URL}/news/${id}` : `${API_URL}/news`;
            try {
                await fetchProtected(url, { method, body: JSON.stringify(payload) });
                window.showStatus('Новину збережено!');
                document.getElementById('news-id').value = '';
                if (fileInput) fileInput.value = '';
                window.loadNews();
                window.updateDashboardStats();
            } catch(e) { console.error('Помилка збереження новини:', e); window.showStatus('Помилка при збереженні новини', true); }
        });
    }

    // Docs-форма
    const docsForm = document.getElementById('docs-form');
    if (docsForm) {
        docsForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const title = document.getElementById('doc-title').value;
            const file_type = document.getElementById('doc-type').value;
            const file = document.getElementById('doc-file').files[0];
            if (!file) {
                window.showStatus('Виберіть файл', true);
                return;
            }
            try {
                const formData = new FormData();
                formData.append('file', file);
                const upRes = await fetchProtected(`${API_URL}/upload/document`, { method: 'POST', body: formData });
                const upData = await upRes.json();
                const file_url = upData.url;
                await fetchProtected(`${API_URL}/documents`, { method: 'POST', body: JSON.stringify({ title, file_type, file_url }) });
                document.getElementById('doc-title').value = '';
                document.getElementById('doc-file').value = '';
                window.showStatus('Документ додано!');
                window.loadDocuments();
            } catch(e) { console.error('Помилка завантаження документа:', e); window.showStatus('Помилка при завантаженні документа', true); }
        });
    }

    // Service slug select listener
    const serviceSelect = document.getElementById('service-slug-select');
    if (serviceSelect) {
        // Загружаем первичные данные услуги
        window.loadServiceForSelectedSlug();
        serviceSelect.addEventListener('change', () => {
            window.loadServiceForSelectedSlug();
        });
    }
}

// --- ГЛОБАЛЬНІ ФУНКЦІЇ ДЛЯ HTML (Робимо їх доступними з кнопок) ---
window.logout = function() {
    localStorage.removeItem('bti_token');
    checkAuth();
};

window.openTab = function(tabId) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.sidebar button').forEach(el => el.classList.remove('active'));
    const tabEl = document.getElementById(tabId);
    if (tabEl) {
        tabEl.classList.add('active');
    }
    if (typeof event !== 'undefined' && event.target) {
        event.target.classList.add('active');
    }
    
    if (tabId === 'tab-faq') window.loadFaqs();
    if (tabId === 'tab-news') window.loadNews();
    if (tabId === 'tab-contacts') window.loadContacts();
    if (tabId === 'tab-documents') window.loadDocuments();
    if (tabId === 'tab-requests') window.loadRequests();
    if (tabId === 'tab-team') window.loadTeam();
    if (tabId === 'tab-services') window.loadServiceForSelectedSlug();
};

window.showStatus = function(msg, isError = false) {
    const el = document.getElementById('status-msg');
    el.textContent = msg; 
    el.style.backgroundColor = isError ? '#fee2e2' : '#dcfce7';
    el.style.color = isError ? '#991b1b' : '#166534';
    el.style.display = 'block';
    setTimeout(() => el.style.display = 'none', 3000);
};

function escapeHTML(str) {
    if (!str) return '';
    return str.replace(/[&<>'"]/g, tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag));
}

function renderPagination(totalItems, currentPage, containerId, callbackFunc) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';
    const totalPages = Math.ceil(totalItems / ITEMS_PER_PAGE);
    if (totalPages <= 1) return; 
    for (let i = 1; i <= totalPages; i++) {
        const btn = document.createElement('button');
        btn.className = `page-btn ${i === currentPage ? 'active' : ''}`;
        btn.textContent = i;
        btn.onclick = () => callbackFunc(i);
        container.appendChild(btn);
    }
}

// --- ДАШБОРД ТА НАЛАШТУАННЯ ---
window.loadInitialData = async function() {
    try {
        const res = await fetch(`${API_URL}/settings/hero`);
        const data = await res.json();
        document.getElementById('hero-text').value = data.subtitle || '';
    } catch(e) {}
    window.updateDashboardStats(); 
};

window.updateDashboardStats = async function() {
    try {
        const reqRes = await fetchProtected(`${API_URL}/requests`);
        const requests = await reqRes.json();
        const newsRes = await fetch(`${API_URL}/news`);
        const news = await newsRes.json();
        
        document.getElementById('stat-total-requests').textContent = requests.length;
        document.getElementById('stat-new-requests').textContent = requests.filter(r => r.status === 'Нова' || !r.status).length;
        document.getElementById('stat-news-count').textContent = news.length;
    } catch(e) {}
};

window.updateAdminCredentials = async function() {
    const cp = document.getElementById('sec-current-password').value;
    const nu = document.getElementById('sec-new-username').value;
    const np = document.getElementById('sec-new-password').value;
    if (!cp || !nu || !np) { window.showStatus('Заповніть всі 3 поля', true); return; }
    try {
        await fetchProtected(`${API_URL}/admin/credentials`, { method: 'POST', body: JSON.stringify({ current_password: cp, new_username: nu, new_password: np }) });
        window.showStatus('Дані для входу змінено!');
        document.getElementById('sec-current-password').value = '';
        document.getElementById('sec-new-password').value = '';
    } catch (e) { window.showStatus('Помилка! Невірний старий пароль.', true); }
};

// ОБРОБНИКИ ФОРМ (Прив'язуються автоматично)
document.getElementById('hero-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    try { 
        await fetchProtected(`${API_URL}/settings/hero/update`, { method: 'POST', body: JSON.stringify({ subtitle: document.getElementById('hero-text').value }) }); 
        window.showStatus('Текст збережено!'); 
    } catch(e) {}
});

// --- КОНТАКТИ ---
window.loadContacts = async function() {
    try {
        const res = await fetch(`${API_URL}/settings`);
        const s = await res.json();
        document.getElementById('c-address').value = s.address || '';
        document.getElementById('c-phone-raw').value = s.phone1_raw || '';
        document.getElementById('c-phone-display').value = s.phone1_display || '';
        document.getElementById('c-email').value = s.email || '';
        document.getElementById('c-schedule').value = s.schedule || '';
        document.getElementById('c-telegram').value = s.telegram || '';
        document.getElementById('c-viber').value = s.viber || '';
    } catch(e) {}
};

document.getElementById('contacts-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = { settings: {
        address: document.getElementById('c-address').value, phone1_raw: document.getElementById('c-phone-raw').value, phone1_display: document.getElementById('c-phone-display').value,
        email: document.getElementById('c-email').value, schedule: document.getElementById('c-schedule').value, telegram: document.getElementById('c-telegram').value, viber: document.getElementById('c-viber').value
    }};
    try {
        await fetchProtected(`${API_URL}/settings/bulk-update`, { method: 'POST', body: JSON.stringify(data) });
        window.showStatus('Контакти оновлено!');
    } catch(e) {}
});

// --- ЗАЯВКИ (CRM) ---
let allRequestsData = [];
window.loadRequests = async function() {
    try {
        const res = await fetchProtected(`${API_URL}/requests`);
        allRequestsData = await res.json();
        window.renderRequestsPage(1); 
    } catch(e) {}
};

window.renderRequestsPage = function(page) {
    const list = document.getElementById('requests-list');
    list.innerHTML = '';
    if (allRequestsData.length === 0) { list.innerHTML = '<p>Нових заявок немає.</p>'; return; }
    
    const start = (page - 1) * ITEMS_PER_PAGE;
    allRequestsData.slice(start, start + ITEMS_PER_PAGE).forEach(r => {
        const borderColor = r.status === 'В роботі' ? '#f59e0b' : (r.status === 'Завершено' ? '#10b981' : (r.status === 'Відмова' ? '#ef4444' : '#0ea5e9'));
        list.innerHTML += `<div class="list-item" style="border-left: 5px solid ${borderColor};">
            <div class="req-card">
                <div class="req-info">
                    <strong style="font-size: 16px;">${escapeHTML(r.name)}</strong> 
                    <span style="color:#64748b; font-size:13px; margin-left: 10px;">🕒 ${r.date_str}</span>
                    <div style="margin-top: 8px;"><span style="font-size: 15px; font-weight: 500;">📞 <a href="tel:${escapeHTML(r.phone)}" style="color: #0f172a; text-decoration: none;">${escapeHTML(r.phone)}</a></span></div>
                </div>
                <div class="req-controls">
                    <select onchange="updateRequestStatus(${r.id}, this.value)" style="padding: 8px 10px; font-weight: 600; border-color: ${borderColor}; border-width: 2px; border-radius: 6px;">
                        <option value="Нова" ${r.status === 'Нова' || !r.status ? 'selected' : ''}>🔵 Нова</option>
                        <option value="В роботі" ${r.status === 'В роботі' ? 'selected' : ''}>🟠 В роботі</option>
                        <option value="Завершено" ${r.status === 'Завершено' ? 'selected' : ''}>🟢 Завершено</option>
                        <option value="Відмова" ${r.status === 'Відмова' ? 'selected' : ''}>🔴 Відмова</option>
                    </select>
                    <button class="action-btn del-btn" onclick="deleteRequest(${r.id})">Видалити</button>
                </div>
            </div>
            <p style="margin-top: 15px; font-size: 15px; background: #f8fafc; padding: 12px; border-radius: 6px;">${r.message ? escapeHTML(r.message) : '<em>Без повідомлення</em>'}</p>
        </div>`;
    });
    renderPagination(allRequestsData.length, page, 'requests-pagination', window.renderRequestsPage);
};

window.updateRequestStatus = async function(id, newStatus) {
    try { await fetchProtected(`${API_URL}/requests/${id}/status`, { method: 'PUT', body: JSON.stringify({ status: newStatus }) }); window.loadRequests(); } catch (e) {}
};
window.deleteRequest = async function(id) {
    if(confirm("Видалити заявку?")) { try { await fetchProtected(`${API_URL}/requests/${id}`, { method: 'DELETE' }); window.loadRequests(); } catch(e) {} }
};

// --- FAQ ---
window.loadFaqs = async function() {
    try {
        const res = await fetch(`${API_URL}/faqs`);
        const faqs = await res.json();
        const list = document.getElementById('faq-list');
        if (!list) return;
        list.innerHTML = '';
        if (!faqs.length) {
            list.innerHTML = '<p>FAQ ще не додано.</p>';
            return;
        }
        faqs.forEach(f => {
            const item = document.createElement('div');
            item.className = 'list-item';
            item.innerHTML = `
                <strong>${escapeHTML(f.question)}</strong>
                <p>${escapeHTML(f.answer)}</p>
                <button class="action-btn del-btn" onclick="deleteFaq(${f.id})">Видалити</button>
            `;
            list.appendChild(item);
        });
    } catch(e) {}
};

window.deleteFaq = async function(id) {
    if (!confirm('Видалити питання?')) return;
    try {
        await fetchProtected(`${API_URL}/faqs/${id}`, { method: 'DELETE' });
        window.loadFaqs();
    } catch(e) {}
};

// --- ПОСЛУГИ ТА ЦІНИ ---
window.loadServiceForSelectedSlug = async function() {
    const select = document.getElementById('service-slug-select');
    if (!select) return;
    const slug = select.value;
    try {
        const res = await fetch(`${API_URL}/services/${slug}`);
        const data = await res.json();
        const titleEl = document.getElementById('service-title');
        const tableEl = document.getElementById('service-table-raw');
        if (!titleEl || !tableEl) return;
        titleEl.value = data.title || '';
        const rows = (data.table_data || []).map(r => r.join('; ')).join('\n');
        tableEl.value = rows;
    } catch(e) { console.error('Помилка завантаження послуги:', e); }
};

// --- НОВИНИ ---
window.loadNews = async function() {
    try {
        const res = await fetch(`${API_URL}/news`);
        const items = await res.json();
        const list = document.getElementById('news-list');
        if (!list) return;
        list.innerHTML = '';
        if (!items.length) {
            list.innerHTML = '<p>Новин поки немає.</p>';
            return;
        }
        items.forEach(n => {
            const div = document.createElement('div');
            div.className = 'list-item';
            div.innerHTML = `
                <strong>${escapeHTML(n.title)}</strong>
                <div style="font-size:13px;color:#64748b;margin:4px 0;">${escapeHTML(n.date_str || '')} • ${escapeHTML(n.tag || '')}</div>
                <p>${escapeHTML(n.preview || '')}</p>
                <button class="action-btn" onclick="editNews(${n.id})">Редагувати</button>
                <button class="action-btn del-btn" onclick="deleteNews(${n.id})">Видалити</button>
            `;
            list.appendChild(div);
        });
    } catch(e) { console.error('Помилка завантаження новин:', e); }
};

window.editNews = async function(id) {
    try {
        const res = await fetch(`${API_URL}/news/${id}`);
        const n = await res.json();
        document.getElementById('news-id').value = n.id;
        document.getElementById('news-title').value = n.title || '';
        document.getElementById('news-date').value = n.date_str || '';
        document.getElementById('news-tag').value = n.tag || '';
        document.getElementById('news-preview').value = n.preview || '';
        if (quill) quill.root.innerHTML = n.content || '';
        window.showStatus('Редагуємо новину: ' + n.title);
    } catch(e) { console.error('Помилка редагування новини:', e); window.showStatus('Помилка при завантаженні новини', true); }
};

window.deleteNews = async function(id) {
    if (!confirm('Видалити новину?')) return;
    try {
        await fetchProtected(`${API_URL}/news/${id}`, { method: 'DELETE' });
        window.loadNews();
        window.updateDashboardStats();
    } catch(e) { console.error('Помилка видалення новини:', e); }
};

// --- ДОКУМЕНТИ ---
window.loadDocuments = async function() {
    try {
        const res = await fetchProtected(`${API_URL}/documents`);
        const docs = await res.json();
        const list = document.getElementById('docs-list');
        if (!list) return;
        list.innerHTML = '';
        if (!docs.length) {
            list.innerHTML = '<p>Документів ще немає.</p>';
            return;
        }
        docs.forEach(d => {
            const div = document.createElement('div');
            div.className = 'list-item';
            div.innerHTML = `
                <strong>${escapeHTML(d.title)}</strong>
                <div style="font-size:13px;color:#64748b;">${escapeHTML(d.file_type || '')}</div>
                <a href="${escapeHTML(d.file_url)}" target="_blank">Відкрити</a>
                <button class="action-btn del-btn" onclick="deleteDocument(${d.id})">Видалити</button>
            `;
            list.appendChild(div);
        });
    } catch(e) { console.error('Помилка завантаження документів:', e); }
};

window.deleteDocument = async function(id) {
    if (!confirm('Видалити документ?')) return;
    try {
        await fetchProtected(`${API_URL}/documents/${id}`, { method: 'DELETE' });
        window.loadDocuments();
    } catch(e) { console.error('Помилка видалення документа:', e); }
};

// --- КОМАНДА ---
window.loadTeam = async function() {
    try {
        const res = await fetch(`${API_URL}/team`);
        const team = await res.json();
        const list = document.getElementById('team-list');
        if (!list) return;
        list.innerHTML = '';
        if (!team.length) {
            list.innerHTML = '<p>Команда ще не додана.</p>';
            return;
        }
        team.forEach(m => {
            const div = document.createElement('div');
            div.className = 'list-item';
            div.innerHTML = `
                <div style="display:flex;align-items:center;gap:12px;">
                    ${m.image_url ? `<img src="${escapeHTML(m.image_url)}" alt="" style="width:60px;height:60px;border-radius:999px;object-fit:cover;">` : ''}
                    <div>
                        <strong>${escapeHTML(m.name)}</strong>
                        <div style="font-size:13px;color:#64748b;">${escapeHTML(m.position || '')}</div>
                    </div>
                </div>
                <p style="margin-top:8px;">${escapeHTML(m.description || '')}</p>
                <button class="action-btn" onclick="editTeamMember(${m.id})">Редагувати</button>
                <button class="action-btn del-btn" onclick="deleteTeamMember(${m.id})">Видалити</button>
            `;
            list.appendChild(div);
        });
    } catch(e) {}
};

window.editTeamMember = async function(id) {
    try {
        const res = await fetch(`${API_URL}/team/${id}`);
        const m = await res.json();
        document.getElementById('team-id').value = m.id;
        document.getElementById('team-name').value = m.name || '';
        document.getElementById('team-position').value = m.position || '';
        document.getElementById('team-description').value = m.description || '';
        window.showStatus('Редагуємо: ' + m.name);
    } catch(e) {}
};

window.deleteTeamMember = async function(id) {
    if (!confirm('Видалити спеціаліста?')) return;
    try {
        await fetchProtected(`${API_URL}/team/${id}`, { method: 'DELETE' });
        window.loadTeam();
    } catch(e) {}
};

document.getElementById('team-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const id = document.getElementById('team-id').value;
    const name = document.getElementById('team-name').value;
    const position = document.getElementById('team-position').value;
    const description = document.getElementById('team-description').value;
    const file = document.getElementById('team-image').files[0];

    let image_url = '';
    if (file) {
        try {
            image_url = await window.uploadImageFile(file);
        } catch(e) {
            window.showStatus('Не вдалося завантажити фото', true);
            return;
        }
    }

    const payload = { name, position, description, image_url };
    const method = id ? 'PUT' : 'POST';
    const url = id ? `${API_URL}/team/${id}` : `${API_URL}/team`;
    try {
        await fetchProtected(url, { method, body: JSON.stringify(payload) });
        document.getElementById('team-id').value = '';
        document.getElementById('team-image').value = '';
        window.showStatus('Дані по команді збережено!');
        window.loadTeam();
    } catch(e) {}
});

// Завантаження файлів (Спільне)
window.uploadImageFile = async function(file) {
    const formData = new FormData(); formData.append("file", file);
    const res = await fetchProtected(`${API_URL}/upload`, { method: 'POST', body: formData });
    if (!res.ok) throw new Error('Помилка завантаження');
    const data = await res.json(); return data.url;
};

// ... ТУТ ІДЕ ВАШ СТАРИЙ КОД ДЛЯ НОВИН ТА КОМАНДИ (Додайте window. до назв функцій) ...s