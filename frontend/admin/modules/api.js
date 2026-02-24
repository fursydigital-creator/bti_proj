// api.js
export const CONFIG = {
    API_URL: (window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost') 
        ? 'http://127.0.0.1:8000/api' 
        : '/api',
    TOKEN_KEY: 'bti_admin_token'
};

export class ApiClient {
    static getHeaders() {
        const token = localStorage.getItem(CONFIG.TOKEN_KEY);
        return {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        };
    }

    static async request(endpoint, options = {}) {
        const url = `${CONFIG.API_URL}${endpoint}`;
        try {
            const response = await fetch(url, {
                ...options,
                headers: { ...this.getHeaders(), ...options.headers }
            });
            
            if (response.status === 401) {
                localStorage.removeItem(CONFIG.TOKEN_KEY);
                window.location.href = 'login.html';
                throw new Error('Сесію завершено');
            }
            
            if (!response.ok) {
                const err = await response.json().catch(() => ({}));
                throw new Error(err.detail || 'Помилка сервера');
            }
            
            return await response.json();
        } catch (error) {
            console.error(`[API Error] ${endpoint}:`, error);
            throw error;
        }
    }

    static get(endpoint) { return this.request(endpoint); }
    static post(endpoint, data) { return this.request(endpoint, { method: 'POST', body: JSON.stringify(data) }); }
    static put(endpoint, data) { return this.request(endpoint, { method: 'PUT', body: JSON.stringify(data) }); }
    static delete(endpoint) { return this.request(endpoint, { method: 'DELETE' }); }
    
    // Окремий метод для файлів (multipart/form-data)
    static async uploadFile(endpoint, file) {
        const formData = new FormData();
        formData.append('file', file);
        const token = localStorage.getItem(CONFIG.TOKEN_KEY);
        
        const response = await fetch(`${CONFIG.API_URL}${endpoint}`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
        });
        
        if (!response.ok) throw new Error('Помилка завантаження файлу');
        return await response.json();
    }
}