// contacts.js — Єдиний файл для всіх контактних даних сайту

const SITE_DATA = {
    // Телефони
    phone1: {
        raw: "+380988144214",       // Для посилання (без пробілів)
        display: "(098) 814-42-14"  // Для відображення на екрані
    },

    // Інші контакти
    email: "vusokuy24@gmail.com",
    address: "с.Фурси, вул. Ярослава Мудрого 24",
    
    // Месенджери
    telegramUrl: "https://t.me/kp_bti_fsr",
    viberUrl: "viber://chat?number=%2B380988144214"
};

// Скрипт, який автоматично розставляє ці дані по сторінці після її завантаження
document.addEventListener("DOMContentLoaded", () => {
    
    // Вставляємо Телефон 1 (Посилання та Текст)
    document.querySelectorAll('.var-phone1-link').forEach(el => el.href = `tel:${SITE_DATA.phone1.raw}`);
    document.querySelectorAll('.var-phone1-text').forEach(el => el.textContent = SITE_DATA.phone1.display);

    // Вставляємо Email
    document.querySelectorAll('.var-email-link').forEach(el => el.href = `mailto:${SITE_DATA.email}`);
    document.querySelectorAll('.var-email-text').forEach(el => el.textContent = SITE_DATA.email);

    // Вставляємо Адресу
    document.querySelectorAll('.var-address-text').forEach(el => el.textContent = SITE_DATA.address);

    // Вставляємо Месенджери
    document.querySelectorAll('.var-telegram-link').forEach(el => el.href = SITE_DATA.telegramUrl);
    document.querySelectorAll('.var-viber-link').forEach(el => el.href = SITE_DATA.viberUrl);
    
});