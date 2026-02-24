// modules/core.js
export const API_URL = (window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost') 
    ? 'http://127.0.0.1:8000/api' : '/api';

export function checkAuth() {
    const token = localStorage.getItem('bti_token');
    const loginScreen = document.getElementById('login-screen');
    const adminScreen = document.getElementById('admin-screen');
    
    if (token) {
        if (loginScreen) loginScreen.style.display = 'none';
        if (adminScreen) adminScreen.style.display = 'flex'; // Миттєво показуємо адмінку
        return true;
    } else {
        if (loginScreen) loginScreen.style.display = 'flex';
        if (adminScreen) adminScreen.style.display = 'none';
        return false;
    }
}

export async function fetchProtected(url, options = {}) {
    const token = localStorage.getItem('bti_token');
    if (!options.headers) options.headers = {};
    options.headers['Authorization'] = `Bearer ${token}`;
    
    if (!(options.body instanceof FormData)) {
        options.headers['Content-Type'] = 'application/json';
    }
    
    const response = await fetch(url, options);
    if (response.status === 401) { 
        localStorage.removeItem('bti_token'); 
        checkAuth(); 
        alert("Сесія завершена. Увійдіть знову."); 
        throw new Error("Unauthorized"); 
    }
    if (!response.ok) throw new Error(`Помилка сервера: ${response.status}`);
    return response;
}