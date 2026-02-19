document.addEventListener("DOMContentLoaded", async () => {
    const API_URL = 'http://127.0.0.1:8000/api';

    try {
        const response = await fetch(`${API_URL}/settings`);
        const s = await response.json();

        // Заповнюємо дані на сторінці, якщо вони є в базі
        if (s.phone1_raw) {
            document.querySelectorAll('.var-phone1-link').forEach(el => el.href = `tel:${s.phone1_raw}`);
        }
        if (s.phone1_display) {
            document.querySelectorAll('.var-phone1-text').forEach(el => el.textContent = s.phone1_display);
        }
        if (s.email) {
            document.querySelectorAll('.var-email-link').forEach(el => el.href = `mailto:${s.email}`);
            document.querySelectorAll('.var-email-text').forEach(el => el.textContent = s.email);
        }
        if (s.address) {
            document.querySelectorAll('.var-address-text').forEach(el => el.textContent = s.address);
        }
        if (s.telegram) {
            document.querySelectorAll('.var-telegram-link').forEach(el => el.href = s.telegram);
        }
        if (s.viber) {
            document.querySelectorAll('.var-viber-link').forEach(el => el.href = s.viber);
        }
        
        // Спеціальне поле для графіка (якщо воно є в HTML)
        const scheduleEl = document.getElementById('var-schedule');
        if (scheduleEl && s.schedule) {
            // Перетворюємо переноси рядків у <br> для HTML
            scheduleEl.innerHTML = s.schedule.replace(/\n/g, '<br>');
        }

    } catch (error) {
        console.error("Не вдалося завантажити контакти з сервера:", error);
    }
});