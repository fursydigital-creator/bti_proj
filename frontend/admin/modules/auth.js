// auth.js
import { ApiClient, CONFIG } from './api.js';

export class AuthManager {
    static async login(username, password) {
        try {
            const response = await fetch(`${CONFIG.API_URL}/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            if (!response.ok) {
                throw new Error('Невірний логін або пароль');
            }

            const data = await response.json();
            localStorage.setItem(CONFIG.TOKEN_KEY, data.access_token);
            return true;
        } catch (error) {
            console.error('Помилка логіну:', error);
            throw error;
        }
    }

    static logout() {
        localStorage.removeItem(CONFIG.TOKEN_KEY);
        window.location.reload();
    }

    static isLoggedIn() {
        return !!localStorage.getItem(CONFIG.TOKEN_KEY);
    }

    static checkAuth() {
        const loggedIn = this.isLoggedIn();
        const loginScreen = document.getElementById('login-screen');
        const adminScreen = document.getElementById('admin-screen');

        console.log('checkAuth() - loggedIn:', loggedIn, 'loginScreen:', loginScreen, 'adminScreen:', adminScreen);

        // Видаляємо класи спочатку
        if (loginScreen) {
            loginScreen.classList.remove('logged-in');
            if (adminScreen) adminScreen.classList.remove('logged-in');
        }

        // Додаємо клас залежно від стану логіну
        if (loggedIn) {
            console.log('Adding logged-in class');
            if (loginScreen) loginScreen.classList.add('logged-in');
            if (adminScreen) adminScreen.classList.add('logged-in');
        }

        return loggedIn;
    }
}

// Обробник форми логіну
export function initLoginForm() {
    const loginForm = document.getElementById('login-form');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const loginError = document.getElementById('login-error');

    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            try {
                await AuthManager.login(usernameInput.value, passwordInput.value);
                AuthManager.checkAuth();
                usernameInput.value = '';
                passwordInput.value = '';
                loginError.style.display = 'none';
            } catch (error) {
                loginError.textContent = error.message;
                loginError.style.display = 'block';
            }
        });
    }
}

// Обробник виходу
export function initLogoutButtons() {
    document.querySelectorAll('[data-action="logout"]').forEach(btn => {
        btn.addEventListener('click', () => AuthManager.logout());
    });
}
