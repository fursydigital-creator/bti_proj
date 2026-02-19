document.addEventListener("DOMContentLoaded", async () => {
    try {
        // Звертаємось до нашої бази даних (поки що на локальному сервері)
        const response = await fetch('http://127.0.0.1:8000/api/settings');
        
        if (!response.ok) {
            throw new Error("Помилка завантаження контактів з API");
        }
        
        const data = await response.json();

        // Беремо дані з бази, а якщо поле там пусте — підставляємо дефолтне значення
        const phoneRaw = data.phone1_raw || "+380980000000";
        const phoneDisplay = data.phone1_display || "(098) 000-00-00";
        const telegramUrl = data.telegram || "#";
        const viberUrl = data.viber || "#";
        const address = data.address || "с. Фурси";
        const email = data.email || "info@bti-expert.com";
        const schedule = data.schedule || "Пн-Пт: 09:00 - 18:00";

        // Розумна функція, яка шукає всі елементи на сторінці і оновлює їх
        const updateElements = (selector, attribute, value) => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => {
                if (attribute === 'textContent') {
                    el.textContent = value;
                } else {
                    el.setAttribute(attribute, value);
                }
            });
        };

        // Оновлюємо ТЕЛЕФОНИ (в шапці, футері, на сторінках послуг)
        updateElements('.var-phone1-link', 'href', `tel:${phoneRaw}`);
        updateElements('.var-phone1-text', 'textContent', phoneDisplay);
        
        // Оновлюємо МЕСЕНДЖЕРИ
        updateElements('.var-telegram-link', 'href', telegramUrl);
        updateElements('.var-viber-link', 'href', viberUrl);
        
        // Оновлюємо ІНШІ ДАНІ (для футера або сторінки контактів)
        updateElements('.var-address-text', 'textContent', address);
        updateElements('.var-email-link', 'href', `mailto:${email}`);
        updateElements('.var-email-text', 'textContent', email);
        updateElements('.var-schedule-text', 'textContent', schedule);

    } catch (error) {
        console.error("Бекенд недоступний. Використовуються стандартні контакти HTML.", error);
    }
});