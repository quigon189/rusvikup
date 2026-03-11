// Отправка формы
document.getElementById('carEvaluationForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);

    // Используем существующий контейнер для сообщений или создаём новый
    let statusDiv = form.querySelector('.mt-3');
    if (!statusDiv) {
        statusDiv = document.createElement('div');
        statusDiv.className = 'mt-3';
        form.appendChild(statusDiv);
    }

    const btn = form.querySelector('button[type="submit"]');
    btn.disabled = true;
    btn.textContent = 'Отправка...';

    try {
        // Замените URL на адрес вашего бэкенда
        const response = await fetch('https://functions.yandexcloud.net/d4e48dnd65n2mo92fb2s', {
            method: 'POST',
            body: formData
        });
        const result = await response.json();
        if (response.ok) {
            statusDiv.innerHTML = '<div class="alert alert-success">Заявка отправлена! Мы перезвоним в течение 5 минут.</div>';
            form.reset();
        } else {
            statusDiv.innerHTML = `<div class="alert alert-danger">Ошибка: ${result.error || 'Повторите попытку'}</div>`;
        }
    } catch (error) {
        statusDiv.innerHTML = '<div class="alert alert-danger">Ошибка сети. Проверьте соединение.</div>';
    } finally {
        btn.disabled = false;
        btn.textContent = 'УЗНАТЬ СТОИМОСТЬ АВТО';
    }
});
