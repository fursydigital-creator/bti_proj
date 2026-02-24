// admin.js
import { CrudController } from './crud.js';
import { AuthManager, initLoginForm, initLogoutButtons } from './auth.js';

// Перевірка аутентифікації при завантаженні
document.addEventListener('DOMContentLoaded', () => {
    AuthManager.checkAuth();
    initLoginForm();
    initLogoutButtons();
    
    // Якщо не залогінений, виходимо
    if (!AuthManager.isLoggedIn()) {
        return;
    }
    
    // 1. Ініціалізація новин
    const newsController = new CrudController({
        endpoint: '/news',
        tableId: 'news-table',
        formId: 'news-form',
        modalId: 'news-modal',
        paginationId: 'news-pagination',
        renderRowFn: (news) => `
            <tr>
                <td>${news.id}</td>
                <td><img src="${news.image_url}" width="50" style="border-radius:4px;"></td>
                <td>${news.title}</td>
                <td>${news.date_str}</td>
                <td>
                    <button class="btn-sm btn-edit" data-action="edit" data-id="${news.id}">Редагувати</button>
                    <button class="btn-sm btn-delete" data-action="delete" data-id="${news.id}">Видалити</button>
                </td>
            </tr>
        `
    });

    // 2. Ініціалізація команди
    const teamController = new CrudController({
        endpoint: '/team',
        tableId: 'team-table',
        formId: 'team-form',
        modalId: 'team-modal',
        paginationId: 'team-pagination',
        renderRowFn: (member) => `
            <tr>
                <td><img src="${member.image_url}" width="40" style="border-radius:50%;"></td>
                <td>${member.name}</td>
                <td>${member.position}</td>
                <td>
                    <button class="btn-sm btn-edit" data-action="edit" data-id="${member.id}">✎</button>
                    <button class="btn-sm btn-delete" data-action="delete" data-id="${member.id}">×</button>
                </td>
            </tr>
        `
    });

    // 3. Ініціалізація FAQ
    const faqController = new CrudController({
        endpoint: '/faqs',
        tableId: 'faq-table',
        formId: 'faq-form',
        modalId: 'faq-modal',
        paginationId: 'faq-pagination',
        renderRowFn: (faq) => `
            <tr>
                <td>${faq.id}</td>
                <td>${faq.question}</td>
                <td>
                    <button class="btn-sm btn-delete" data-action="delete" data-id="${faq.id}">Видалити</button>
                </td>
            </tr>
        `
    });

    // Завантаження всіх даних
    newsController.load();
    teamController.load();
    faqController.load();

    // Прив'язка кнопок "Додати" до відкриття модалок
    document.getElementById('btn-add-news')?.addEventListener('click', () => newsController.openModal());
    document.getElementById('btn-add-team')?.addEventListener('click', () => teamController.openModal());
    document.getElementById('btn-add-faq')?.addEventListener('click', () => faqController.openModal());
    
    // Закриття модалок (делегування на рівні overlay або кнопок .close-btn)
    document.querySelectorAll('.close-btn').forEach(btn => {
        btn.onclick = (e) => {
            const modal = e.target.closest('.modal');
            modal.classList.remove('active');
            document.getElementById('modal-overlay').classList.remove('active');
        };
    });
});

// Глобальна функція для переключення табів (для onclick у HTML)
window.openTab = function(tabId) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.sidebar button').forEach(el => el.classList.remove('active'));
    
    const tab = document.getElementById(tabId);
    if (tab) {
        tab.classList.add('active');
    }
    
    event.target?.classList.add('active');
};
