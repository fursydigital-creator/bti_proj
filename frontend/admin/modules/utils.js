// utils.js

// --- ПАГІНАЦІЯ ---
export class Pagination {
    constructor(itemsPerPage = 10) {
        this.itemsPerPage = itemsPerPage;
        this.currentPage = 1;
        this.data = [];
    }

    setData(data) {
        this.data = data;
        this.currentPage = 1;
    }

    get totalPages() { return Math.ceil(this.data.length / this.itemsPerPage) || 1; }
    
    getCurrentPageData() {
        const start = (this.currentPage - 1) * this.itemsPerPage;
        return this.data.slice(start, start + this.itemsPerPage);
    }

    renderControls(containerId, onPageChange) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        container.innerHTML = `
            <div class="pagination-controls" style="display: flex; gap: 15px; align-items: center; justify-content: center; margin-top: 20px;">
                <button class="btn-base btn-outline" ${this.currentPage === 1 ? 'disabled' : ''} id="prev-${containerId}">← Попередня</button>
                <span>Сторінка ${this.currentPage} з ${this.totalPages}</span>
                <button class="btn-base btn-outline" ${this.currentPage === this.totalPages ? 'disabled' : ''} id="next-${containerId}">Наступна →</button>
            </div>
        `;

        document.getElementById(`prev-${containerId}`)?.addEventListener('click', () => {
            if (this.currentPage > 1) { this.currentPage--; onPageChange(); }
        });
        document.getElementById(`next-${containerId}`)?.addEventListener('click', () => {
            if (this.currentPage < this.totalPages) { this.currentPage++; onPageChange(); }
        });
    }
}

// --- РОБОТА З ФОРМАМИ ТА UI ---
export class UIManager {
    static fillForm(formId, data) {
        const form = document.getElementById(formId);
        if (!form) return;
        
        Object.keys(data).forEach(key => {
            const input = form.elements[key];
            if (input) {
                if (input.type === 'checkbox') input.checked = data[key];
                else input.value = data[key];
            }
        });
        form.dataset.editId = data.id; // Зберігаємо ID для редагування
    }

    static getFormData(formId) {
        const form = document.getElementById(formId);
        const data = Object.fromEntries(new FormData(form).entries());
        const id = form.dataset.editId;
        return { id, data };
    }

    static clearForm(formId) {
        const form = document.getElementById(formId);
        if (form) {
            form.reset();
            delete form.dataset.editId;
        }
    }

    static toggleModal(modalId, show) {
        const modal = document.getElementById(modalId);
        const overlay = document.getElementById('modal-overlay'); // Має бути один на всю сторінку
        if (show) {
            modal?.classList.add('active');
            overlay?.classList.add('active');
        } else {
            modal?.classList.remove('active');
            overlay?.classList.remove('active');
        }
    }
}