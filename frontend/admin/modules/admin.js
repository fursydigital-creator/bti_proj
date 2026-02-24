// modules/admin.js
import { API_URL, checkAuth, fetchProtected } from './core.js';

const ITEMS_PER_PAGE = 5; 

// --- ІНІЦІАЛІЗАЦІЯ ЛОГІНУ (БЕЗ ПЕРЕЗАВАНТАЖЕННЯ СТОРІНКИ) ---
document.addEventListener('DOMContentLoaded', () => {
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
});

// --- ГЛОБАЛЬНІ ФУНКЦІЇ ДЛЯ HTML (Робимо їх доступними з кнопок) ---
window.logout = function() {
    localStorage.removeItem('bti_token');
    checkAuth();
};

window.openTab = function(tabId) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.sidebar button').forEach(el => el.classList.remove('active'));
    document.getElementById(tabId).classList.add('active');
    event.target.classList.add('active');
    
    if (tabId === 'tab-faq') window.loadFaqs();
    if (tabId === 'tab-news') window.loadNews();
    if (tabId === 'tab-contacts') window.loadContacts();
    if (tabId === 'tab-documents') window.loadDocuments();
    if (tabId === 'tab-requests') window.loadRequests();
    if (tabId === 'tab-team') window.loadTeam();
};

window.showStatus = function(msg, isError = false) {
    const el = document.getElementById('status-msg');
    el.textContent = msg; 
    el.style.backgroundColor = isError ? '#fee2e2' : '#dcfce7';
    el.style.color = isError ? '#991b1b' : '#166534';
    el.style.display = 'block';
    setTimeout(() => el.style.display = 'none', 3000);
};

// Редактор Quill
const quill = new Quill('#quill-editor', {
    theme: 'snow',
    placeholder: 'Напишіть вашу статтю тут...',
    modules: { toolbar: [ [{ 'header': [2, 3, false] }], ['bold', 'italic', 'underline'], [{ 'list': 'ordered'}, { 'list': 'bullet' }], ['link'], ['clean'] ] }
});

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

// Додайте аналогічні `window.loadNews`, `window.deleteNews`, `window.loadTeam` для іншого функціоналу (так як у вас було в старому файлі, просто додайте window. спереду).

// Завантаження файлів (Спільне)
window.uploadImageFile = async function(file) {
    const formData = new FormData(); formData.append("file", file);
    const res = await fetchProtected(`${API_URL}/upload`, { method: 'POST', body: formData });
    if (!res.ok) throw new Error('Помилка завантаження');
    const data = await res.json(); return data.url;
};

// ... ТУТ ІДЕ ВАШ СТАРИЙ КОД ДЛЯ НОВИН ТА КОМАНДИ (Додайте window. до назв функцій) ...s