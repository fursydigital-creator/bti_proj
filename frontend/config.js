/**
 * Базовий URL API: локальна розробка (127.0.0.1, localhost, file:) або продакшен.
 */
const API_URL = (window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost' || window.location.protocol === 'file:')
    ? 'http://127.0.0.1:8000/api'
    : '/api';
