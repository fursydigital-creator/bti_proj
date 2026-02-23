const ITEMS_PER_PAGE = 5; 

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
        
        const quill = new Quill('#quill-editor', {
            theme: 'snow',
            placeholder: 'Напишіть вашу статтю тут...',
            modules: {
                toolbar: [
                    [{ 'header': [2, 3, false] }],
                    ['bold', 'italic', 'underline'],
                    [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                    ['link'],
                    ['clean']
                ]
            }
        });
        function escapeHTML(str) {
    if (!str) return '';
    return str.replace(/[&<>'"]/g, tag => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
    }[tag] || tag));
}
        // --- Виправлено функцію перевірки авторизації (app-screen -> admin-screen) ---
        function checkAuth() {
            const token = localStorage.getItem('bti_token');
            if (token) {
                document.getElementById('login-screen').style.display = 'none';
                document.getElementById('admin-screen').style.display = 'block'; // Виправлено ID та тип display
                loadInitialData();
            } else {
                document.getElementById('login-screen').style.display = 'flex';
                document.getElementById('admin-screen').style.display = 'none'; // Виправлено ID
            }
        }
        
        document.getElementById('login-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const u = document.getElementById('username').value;
            const p = document.getElementById('password').value;
            try {
                const res = await fetch(`${API_URL}/login`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: u, password: p }) });
                if (res.ok) {
                    const data = await res.json();
                    localStorage.setItem('bti_token', data.access_token);
                    document.getElementById('login-error').style.display = 'none';
                    checkAuth();
                } else document.getElementById('login-error').style.display = 'block';
            } catch(err) { console.error(err); }
        });
        
        function logout() { localStorage.removeItem('bti_token'); checkAuth(); }

        async function fetchProtected(url, options = {}) {
            const token = localStorage.getItem('bti_token');
            if (!options.headers) options.headers = {};
            options.headers['Authorization'] = `Bearer ${token}`;
            
            if (!(options.body instanceof FormData)) {
                options.headers['Content-Type'] = 'application/json';
            }
            
            const response = await fetch(url, options);
            if (response.status === 401) { logout(); alert("Сесія завершена. Увійдіть знову."); throw new Error("Unauthorized"); }
            if (!response.ok) { throw new Error(`Помилка сервера: ${response.status}`); }
            
            return response;
        }
        
        async function updateDashboardStats() {
            try {
                // Отримуємо заявки
                const reqRes = await fetchProtected(`${API_URL}/requests`);
                const requests = await reqRes.json();
                
                // Отримуємо новини
                const newsRes = await fetch(`${API_URL}/news`);
                const news = await newsRes.json();

                // Рахуємо
                const totalReq = requests.length;
                const newReq = requests.filter(r => r.status === 'Нова' || !r.status).length;
                const totalNews = news.length;

                // Оновлюємо цифри на екрані
                document.getElementById('stat-total-requests').textContent = totalReq;
                document.getElementById('stat-new-requests').textContent = newReq;
                document.getElementById('stat-news-count').textContent = totalNews;

            } catch(e) { console.error("Помилка статистики", e); }
        }

        // --- ЗМІНА ЛОГІНУ ТА ПАРОЛЮ ---
        async function updateAdminCredentials() {
            const current_password = document.getElementById('sec-current-password').value;
            const new_username = document.getElementById('sec-new-username').value;
            const new_password = document.getElementById('sec-new-password').value;

            // Перевіряємо, чи всі поля заповнені
            if (!current_password || !new_username || !new_password) {
                showStatus('Будь ласка, заповніть всі 3 поля', true);
                return;
            }

            try {
                // Відправляємо запит на сервер
                const res = await fetchProtected(`${API_URL}/admin/credentials`, {
                    method: 'POST',
                    body: JSON.stringify({ 
                        current_password: current_password, 
                        new_username: new_username, 
                        new_password: new_password 
                    })
                });
                
                showStatus('Дані для входу успішно змінено!');
                
                // Очищаємо поля після успішної зміни
                document.getElementById('sec-current-password').value = '';
                document.getElementById('sec-new-password').value = '';
                
            } catch (e) {
                showStatus('Помилка! Можливо, ви ввели неправильний старий пароль.', true);
            }
        }   
        
        function openTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.sidebar button').forEach(el => el.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            event.target.classList.add('active');
            if (tabId === 'tab-faq') loadFaqs();
            if (tabId === 'tab-news') loadNews();
            if (tabId === 'tab-contacts') loadContacts();
            if (tabId === 'tab-documents') loadDocuments();
            if (tabId === 'tab-requests') loadRequests();
        }

        function showStatus(msg, isError = false) {
            const el = document.getElementById('status-msg');
            el.textContent = msg; 
            el.style.backgroundColor = isError ? '#fee2e2' : '#dcfce7';
            el.style.color = isError ? '#991b1b' : '#166534';
            el.style.display = 'block';
            setTimeout(() => el.style.display = 'none', 3000);
        }

        async function loadInitialData() {
            try {
                const res = await fetch(`${API_URL}/settings/hero`);
                const data = await res.json();
                document.getElementById('hero-text').value = data.subtitle || '';
            } catch(e) { console.error("Помилка завантаження головного тексту", e); }
            updateDashboardStats(); 
        }

        document.getElementById('hero-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            try { 
                await fetchProtected(`${API_URL}/settings/hero/update`, { method: 'POST', body: JSON.stringify({ subtitle: document.getElementById('hero-text').value }) }); 
                showStatus('Текст збережено!'); 
            } catch(e) {}
        });
        
        async function loadContacts() {
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
            } catch(e) { console.error("Помилка завантаження контактів", e); }
        }

        document.getElementById('contacts-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const data = {
                settings: {
                    address: document.getElementById('c-address').value,
                    phone1_raw: document.getElementById('c-phone-raw').value,
                    phone1_display: document.getElementById('c-phone-display').value,
                    email: document.getElementById('c-email').value,
                    schedule: document.getElementById('c-schedule').value,
                    telegram: document.getElementById('c-telegram').value,
                    viber: document.getElementById('c-viber').value
                }
            };
            try {
                await fetchProtected(`${API_URL}/settings/bulk-update`, {
                    method: 'POST',
                    body: JSON.stringify(data)
                });
                showStatus('Контакти успішно оновлено!');
            } catch(e) { showStatus('Помилка оновлення', true); }
        });

        let allFaqsData = [];
        let currentFaqPage = 1;

        async function loadFaqs() {
            try {
                const res = await fetch(`${API_URL}/faqs`);
                allFaqsData = await res.json();
                renderFaqPage(currentFaqPage);
            } catch(e) { console.error("Помилка FAQ", e); }
        }

        function renderFaqPage(page) {
            const totalPages = Math.ceil(allFaqsData.length / ITEMS_PER_PAGE);
            if (page > totalPages && totalPages > 0) page = totalPages;
            
            currentFaqPage = page;
            const list = document.getElementById('faq-list');
            list.innerHTML = '';
            
            if (allFaqsData.length === 0) { list.innerHTML = '<p>FAQ порожній.</p>'; return; }
            
            const start = (page - 1) * ITEMS_PER_PAGE;
            const pageItems = allFaqsData.slice(start, start + ITEMS_PER_PAGE);

            pageItems.forEach(f => { 
                list.innerHTML += `<div class="list-item">
                    <button class="action-btn del-btn" onclick="deleteFaq(${f.id})">Видалити</button>
                    <strong>${f.question}</strong><p style="margin-top: 10px; color: #555;">${f.answer}</p>
                </div>`; 
            });
            renderPagination(allFaqsData.length, page, 'faq-pagination', renderFaqPage);
        }
        
        async function deleteFaq(id) { 
            if(confirm("Точно видалити?")) { 
                try { await fetchProtected(`${API_URL}/faqs/${id}`, { method: 'DELETE' }); showStatus('Видалено!'); loadFaqs(); } catch(e) { showStatus('Помилка з\'єднання з сервером', true); } 
            } 
        }
        
        document.getElementById('faq-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            try { 
                await fetchProtected(`${API_URL}/faqs`, { method: 'POST', body: JSON.stringify({ question: document.getElementById('faq-q').value, answer: document.getElementById('faq-a').value }) }); 
                document.getElementById('faq-q').value = ''; 
                document.getElementById('faq-a').value = ''; 
                showStatus('Питання додано!'); 
                loadFaqs(); 
            } catch(e) { showStatus('Помилка з\'єднання з сервером', true); }
        });

        let currentSlug = '';
        async function loadServiceData() {
            currentSlug = document.getElementById('service-select').value;
            if(!currentSlug) return;
            document.getElementById('table-editor').style.display = 'block';
            try {
                const res = await fetch(`${API_URL}/services/${currentSlug}`);
                const data = await res.json();
                document.getElementById('service-title').value = data.title || '';
                const container = document.getElementById('table-container');
                container.innerHTML = ''; 
                const tableData = data.table_data && data.table_data.length > 0 ? data.table_data : [["Послуга", "Ціна"]];
                tableData.forEach((row, index) => addTableRow(row[0], row[1], index === 0));
            } catch(e) { console.error("Помилка завантаження послуги", e); }
        }
        
        function addTableRow(col1Val = '', col2Val = '', isHeader = false) {
            const container = document.getElementById('table-container');
            const rowDiv = document.createElement('div');
            rowDiv.className = `price-row ${isHeader ? 'header-row' : ''}`;
            rowDiv.innerHTML = `<input type="text" class="col-name" value="${col1Val}" placeholder="${isHeader ? 'Назва колонки 1' : 'Назва послуги'}"><input type="text" class="col-price" value="${col2Val}" placeholder="${isHeader ? 'Назва колонки 2' : 'Ціна'}">${!isHeader ? '<button type="button" class="action-btn del-btn" onclick="this.parentElement.remove()">X</button>' : '<div style="width: 44px;"></div>'}`;
            container.appendChild(rowDiv);
        }
        
        async function saveServiceData() {
            const title = document.getElementById('service-title').value;
            const rows = document.querySelectorAll('.price-row');
            const tableData = [];
            rows.forEach(row => tableData.push([row.querySelector('.col-name').value, row.querySelector('.col-price').value]));
            try { 
                await fetchProtected(`${API_URL}/services/${currentSlug}`, { method: 'POST', body: JSON.stringify({ title: title, table_data: tableData }) }); 
                showStatus('Таблицю успішно збережено в базі!'); 
            } catch (error) { showStatus('Помилка з\'єднання з сервером', true); }
        }

        let editingNewsId = null; 
        let allNewsData = []; 
        let currentNewsPage = 1;

        async function loadNews() {
            try {
                const res = await fetch(`${API_URL}/news`);
                allNewsData = await res.json();
                renderNewsPage(1); 
            } catch(e) { console.error("Помилка", e); }
        }

        function renderNewsPage(page) {
            currentNewsPage = page;
            const list = document.getElementById('news-list');
            list.innerHTML = '';
            
            if (allNewsData.length === 0) { list.innerHTML = '<p>Новин поки немає.</p>'; return; }
            
            const start = (page - 1) * ITEMS_PER_PAGE;
            const pageItems = allNewsData.slice(start, start + ITEMS_PER_PAGE);

            pageItems.forEach(n => { 
                list.innerHTML += `<div class="list-item">
                    <button class="action-btn del-btn" onclick="deleteNews(${n.id})">Видалити</button>
                    <button class="action-btn" style="background:#f59e0b; padding: 6px 12px; font-size: 13px; float: right; width: auto; margin-top: 0; margin-right: 10px;" onclick="editNews(${n.id})">Редагувати</button>
                    <strong>${n.title}</strong> <span style="color:#64748b; font-size:13px; margin-left: 10px;">🕒 ${n.date_str}</span>
                    <div style="font-size: 13px; color: #0ea5e9; margin-top: 5px;">#${n.tag}</div>
                </div>`; 
            });

            renderPagination(allNewsData.length, page, 'news-pagination', renderNewsPage);
        }

        async function editNews(id) {
            try {
                const res = await fetch(`${API_URL}/news/${id}`);
                const n = await res.json();
                
                editingNewsId = id;
                document.getElementById('news-title').value = n.title;
                
                const [d, m, y] = n.date_str.split('.');
                document.getElementById('news-date').value = `${y}-${m}-${d}`;
                
                document.getElementById('news-tag').value = n.tag;
                document.getElementById('news-preview').value = n.preview;
                quill.root.innerHTML = n.content;
                
                document.getElementById('news-image-url').value = n.image_url;
                const previewDiv = document.getElementById('image-preview');
                previewDiv.style.display = 'block';
                previewDiv.querySelector('img').src = n.image_url;
                
                document.getElementById('news-submit-btn').textContent = '💾 Оновити новину';
                document.getElementById('news-cancel-btn').style.display = 'block';
                
                document.getElementById('news-form').scrollIntoView({behavior: 'smooth'});
            } catch(e) { console.error("Помилка завантаження новини для редагування", e); }
        }

        function cancelNewsEdit() {
            editingNewsId = null;
            document.getElementById('news-form').reset();
            quill.root.innerHTML = '';
            document.getElementById('news-image-url').value = '';
            document.getElementById('image-preview').style.display = 'none';
            document.getElementById('news-submit-btn').textContent = 'Опублікувати новину';
            document.getElementById('news-cancel-btn').style.display = 'none';
        }

        async function uploadImageFile(file) {
            const formData = new FormData();
            formData.append("file", file);
            
            const res = await fetchProtected(`${API_URL}/upload`, {
                method: 'POST',
                body: formData
            });
            if (!res.ok) throw new Error('Помилка завантаження');
            const data = await res.json();
            return data.url;
        }

        document.getElementById('news-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const articleContent = quill.root.innerHTML;
            if (quill.getText().trim().length === 0) { alert("Текст не може бути порожнім!"); return; }

            const dateInput = document.getElementById('news-date').value;
            const [y, m, d] = dateInput.split('-');
            const formattedDate = `${d}.${m}.${y}`;

            let finalImageUrl = document.getElementById('news-image-url').value;
            const fileInput = document.getElementById('news-image-file');
            
            if (fileInput.files.length > 0) {
                showStatus('Завантаження картинки...', false);
                try {
                    finalImageUrl = await uploadImageFile(fileInput.files[0]);
                } catch(err) {
                    showStatus('Помилка завантаження картинки', true);
                    return;
                }
            } else if (!finalImageUrl) {
                alert("Будь ласка, виберіть картинку!");
                return;
            }

            const newsData = {
                title: document.getElementById('news-title').value,
                date_str: formattedDate,
                tag: document.getElementById('news-tag').value,
                image_url: finalImageUrl,
                preview: document.getElementById('news-preview').value,
                content: articleContent
            };

            try {
                if (editingNewsId) {
                    await fetchProtected(`${API_URL}/news/${editingNewsId}`, { method: 'PUT', body: JSON.stringify(newsData) });
                    showStatus('Новину успішно оновлено!');
                } else {
                    await fetchProtected(`${API_URL}/news`, { method: 'POST', body: JSON.stringify(newsData) });
                    showStatus('Новину успішно опубліковано!');
                }
                
                cancelNewsEdit(); 
                loadNews(); 
            } catch(err) { showStatus('Помилка збереження', true); }
        });

        async function deleteNews(id) {
            if(confirm("Ви дійсно хочете видалити цю новину?")) {
                try {
                    await fetchProtected(`${API_URL}/news/${id}`, { method: 'DELETE' });
                    if (editingNewsId === id) cancelNewsEdit();
                    showStatus('Видалено!');
                    loadNews();
                } catch(e) { showStatus('Помилка з\'єднання з сервером', true); }
            }
        }

        async function loadDocuments() {
            try {
                const res = await fetch(`${API_URL}/documents`);
                const docs = await res.json();
                const list = document.getElementById('doc-list');
                list.innerHTML = '';
                if (docs.length === 0) list.innerHTML = '<p>Документів поки немає.</p>';
                
                docs.forEach(d => {
                    list.innerHTML += `<div class="list-item">
                        <button class="action-btn del-btn" onclick="deleteDocument(${d.id})">Видалити</button>
                        <strong>${d.title}</strong> 
                        <span style="color:#64748b; font-size:13px; margin-left: 10px;">[${d.file_type}]</span>
                        <div style="font-size: 13px; margin-top: 5px;">
                            <a href="${d.file_url}" target="_blank" style="color: #0ea5e9; text-decoration: none;">Переглянути файл ↗</a>
                        </div>
                    </div>`;
                });
            } catch(e) { console.error("Помилка", e); }
        }

        document.getElementById('doc-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const fileInput = document.getElementById('doc-file');
            const titleInput = document.getElementById('doc-title').value;

            if (fileInput.files.length === 0) { alert("Оберіть файл!"); return; }
            
            const file = fileInput.files[0];
            const ext = file.name.split('.').pop().toUpperCase(); 
            const fileType = `${ext} файл`;

            showStatus('Завантаження файлу на сервер...', false);

            try {
                const formData = new FormData();
                formData.append("file", file);
                const uploadRes = await fetchProtected(`${API_URL}/upload/document`, { method: 'POST', body: formData });
                const uploadData = await uploadRes.json();
                const fileUrl = uploadData.url;

                const docData = {
                    title: titleInput,
                    file_type: fileType,
                    file_url: fileUrl
                };

                await fetchProtected(`${API_URL}/documents`, {
                    method: 'POST',
                    body: JSON.stringify(docData)
                });
                
                showStatus('Документ успішно додано!');
                document.getElementById('doc-form').reset();
                loadDocuments();
            } catch(err) {
                showStatus('Помилка збереження документу', true);
            }
        });

        async function deleteDocument(id) {
            if(confirm("Ви дійсно хочете видалити цей документ?")) {
                try {
                    await fetchProtected(`${API_URL}/documents/${id}`, { method: 'DELETE' });
                    showStatus('Видалено!');
                    loadDocuments();
                } catch(e) { showStatus('Помилка з\'єднання з сервером', true); }
            }
        }

        async function deleteRequest(id) {
            if(confirm("Ви дійсно хочете видалити цю заявку?")) {
                try {
                    await fetchProtected(`${API_URL}/requests/${id}`, { method: 'DELETE' });
                    showStatus('Видалено!');
                    loadRequests();
                } catch(e) { showStatus('Помилка з\'єднання з сервером', true); }
            }
        }

        // --- ЗАЯВКИ (CRM) ---
        let allRequestsData = [];
        let currentReqPage = 1;

        async function loadRequests() {
            try {
                const res = await fetchProtected(`${API_URL}/requests`);
                allRequestsData = await res.json();
                renderRequestsPage(currentReqPage); // Залишаємось на тій же сторінці після оновлення
            } catch(e) { console.error("Помилка завантаження заявок", e); }
        }

        // Функція для визначення кольору смужки збоку
        function getStatusColor(status) {
            if (status === 'В роботі') return '#f59e0b'; // Оранжевий
            if (status === 'Завершено') return '#10b981'; // Зелений
            if (status === 'Відмова') return '#ef4444'; // Червоний
            return '#0ea5e9'; // Синій (Нова)
        }

        // Функція для відправки нового статусу на сервер
        async function updateRequestStatus(id, newStatus) {
            try {
                await fetchProtected(`${API_URL}/requests/${id}/status`, {
                    method: 'PUT',
                    body: JSON.stringify({ status: newStatus })
                });
                showStatus('Статус збережено!');
                loadRequests(); // Перемальовуємо список, щоб оновити кольори
            } catch (e) {
                showStatus('Помилка оновлення статусу', true);
            }
        }

        function renderRequestsPage(page) {
            // Захист від пустої сторінки при видаленні останнього елемента
            const totalPages = Math.ceil(allRequestsData.length / ITEMS_PER_PAGE);
            if (page > totalPages && totalPages > 0) page = totalPages; 
            
            currentReqPage = page;
            const list = document.getElementById('requests-list');
            list.innerHTML = '';
            
            if (allRequestsData.length === 0) { list.innerHTML = '<p>Нових заявок поки немає.</p>'; return; }
            
            const start = (page - 1) * ITEMS_PER_PAGE;
            const pageItems = allRequestsData.slice(start, start + ITEMS_PER_PAGE);

            pageItems.forEach(r => {
                const safeName = escapeHTML(r.name);
                const safePhone = escapeHTML(r.phone);
                const msgDisplay = r.message ? escapeHTML(r.message) : '<em>Клієнт не залишив повідомлення</em>';
                const borderColor = getStatusColor(r.status || 'Нова');
                
                list.innerHTML += `<div class="list-item" style="border-left: 5px solid ${borderColor};">
                    <div class="req-card">
                        
                        <div class="req-info">
                            <strong style="font-size: 16px;">${r.name}</strong> 
                            <span style="color:#64748b; font-size:13px; margin-left: 10px;">🕒 ${r.date_str}</span>
                            <div style="margin-top: 8px;">
                                <span style="font-size: 15px; font-weight: 500;">📞 <a href="tel:${r.phone}" style="color: #0f172a; text-decoration: none;">${r.phone}</a></span>
                            </div>
                        </div>

                        <div class="req-controls">
                            <select onchange="updateRequestStatus(${r.id}, this.value)" style="padding: 8px 10px; font-weight: 600; border-color: ${borderColor}; border-width: 2px; cursor: pointer; border-radius: 6px; outline: none; background: #fff;">
                                <option value="Нова" ${r.status === 'Нова' || !r.status ? 'selected' : ''}>🔵 Нова</option>
                                <option value="В роботі" ${r.status === 'В роботі' ? 'selected' : ''}>🟠 В роботі</option>
                                <option value="Завершено" ${r.status === 'Завершено' ? 'selected' : ''}>🟢 Завершено</option>
                                <option value="Відмова" ${r.status === 'Відмова' ? 'selected' : ''}>🔴 Відмова</option>
                            </select>
                            <button class="action-btn del-btn" onclick="deleteRequest(${r.id})">Видалити</button>
                        </div>

                    </div>
                    
                    <p style="margin-top: 15px; font-size: 15px; background: #f8fafc; padding: 12px; border-radius: 6px; border: 1px solid #e2e8f0; margin-bottom: 0;">${msgDisplay}</p>
                </div>`;
            });

            renderPagination(allRequestsData.length, page, 'requests-pagination', renderRequestsPage);
        }

        checkAuth();
    