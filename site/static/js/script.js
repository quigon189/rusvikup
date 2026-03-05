// Отправка формы
document.getElementById('carEvaluationForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);
    const statusDiv = document.createElement('div');
    statusDiv.className = 'mt-3';
    form.appendChild(statusDiv);
    const btn = form.querySelector('button[type="submit"]');
    btn.disabled = true;
    btn.textContent = 'Отправка...';

    try {
        // Замените URL на адрес вашего бэкенда
        const response = await fetch('https://your-api-gateway-url/submit', {
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
