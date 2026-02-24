// crud.js
import { ApiClient } from './api.js';
import { Pagination, UIManager } from './utils.js';

export class CrudController {
    constructor({ endpoint, tableId, formId, modalId, paginationId, renderRowFn }) {
        this.endpoint = endpoint;
        this.tableId = tableId;
        this.formId = formId;
        this.modalId = modalId;
        this.paginationId = paginationId;
        this.renderRowFn = renderRowFn; // Функція, яка знає, як малювати <tr>
        
        this.pagination = new Pagination(10);
        this.initFormListener();
    }

    async load() {
        try {
            const data = await ApiClient.get(this.endpoint);
            this.pagination.setData(data);
            this.render();
        } catch (e) {
            alert('Помилка завантаження даних');
        }
    }

    render() {
        const tbody = document.querySelector(`#${this.tableId} tbody`);
        if (!tbody) return;
        
        const currentData = this.pagination.getCurrentPageData();
        tbody.innerHTML = currentData.map(item => this.renderRowFn(item)).join('');
        
        this.pagination.renderControls(this.paginationId, () => this.render());
        this.attachActionListeners();
    }

    attachActionListeners() {
        const tbody = document.querySelector(`#${this.tableId} tbody`);
        
        // Використовуємо делегування подій замість onclick="editNews(1)" у HTML
        tbody.onclick = async (e) => {
            const btn = e.target.closest('button');
            if (!btn) return;
            
            const id = btn.dataset.id;
            const action = btn.dataset.action;

            if (action === 'edit') this.edit(id);
            if (action === 'delete') this.delete(id);
        };
    }

    openModal() {
        UIManager.clearForm(this.formId);
        UIManager.toggleModal(this.modalId, true);
    }

    async edit(id) {
        const item = this.pagination.data.find(i => i.id == id);
        if (item) {
            UIManager.fillForm(this.formId, item);
            UIManager.toggleModal(this.modalId, true);
        }
    }

    async delete(id) {
        if (!confirm('Ви впевнені, що хочете видалити цей запис?')) return;
        try {
            await ApiClient.delete(`${this.endpoint}/${id}`);
            await this.load(); // Перезавантажуємо таблицю
        } catch (e) {
            alert('Помилка видалення');
        }
    }

    initFormListener() {
        const form = document.getElementById(this.formId);
        if (!form) return;

        form.onsubmit = async (e) => {
            e.preventDefault();
            const { id, data } = UIManager.getFormData(this.formId);
            
            try {
                if (id) await ApiClient.put(`${this.endpoint}/${id}`, data);
                else await ApiClient.post(this.endpoint, data);
                
                UIManager.toggleModal(this.modalId, false);
                UIManager.clearForm(this.formId);
                await this.load();
            } catch (error) {
                alert('Помилка збереження');
            }
        };
    }
}