const API_URL = (window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost' || window.location.protocol === 'file:') 
    ? 'http://127.0.0.1:8000/api' 
    : '/api';

document.addEventListener("DOMContentLoaded", async () => {
    try {
        const response = await fetch(`${API_URL}/settings`);
        
        if (!response.ok) throw new Error("Помилка API");
        
        const data = await response.json();

        const phoneRaw = data.phone1_raw || "+380980000000";
        const phoneDisplay = data.phone1_display || "(098) 000-00-00";
        const telegramUrl = data.telegram || "#";
        const viberUrl = data.viber || "#";
        const address = data.address || "с. Фурси";
        const email = data.email || "info@bti-expert.com";
        const schedule = data.schedule || "Пн-Пт: 09:00 - 18:00";

        const updateElements = (selector, attribute, value) => {
            document.querySelectorAll(selector).forEach(el => {
                if (attribute === 'textContent') el.textContent = value;
                else el.setAttribute(attribute, value);
            });
        };

        updateElements('.var-phone1-link', 'href', `tel:${phoneRaw}`);
        updateElements('.var-phone1-text', 'textContent', phoneDisplay);
        updateElements('.var-telegram-link', 'href', telegramUrl);
        updateElements('.var-viber-link', 'href', viberUrl);
        updateElements('.var-address-text', 'textContent', address);
        updateElements('.var-email-link', 'href', `mailto:${email}`);
        updateElements('.var-email-text', 'textContent', email);
        updateElements('.var-schedule-text', 'textContent', schedule);

    } catch (error) {
        console.error("Бекенд недоступний", error);
    }
});