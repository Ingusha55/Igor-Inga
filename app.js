const WebApp = window.Telegram.WebApp;
WebApp.ready();

function getNews() {
    fetch('/news')
        .then(response => response.json())
        .then(data => {
            document.getElementById('output').innerText = data.news.join('\n');
        })
        .catch(error => {
            document.getElementById('output').innerText = 'Ой, Ингуля, новости не загрузились! 🌟';
        });
}

function getWeather() {
    fetch('/weather')
        .then(response => response.json())
        .then(data => {
            document.getElementById('output').innerText = `Погода: ${data.weather}`;
        });
}

function setAlarm() {
    const time = prompt('Введи время будильника (HH:MM):');
    fetch('/alarm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ time })
    })
        .then(response => response.json())
        .then(data => {
            document.getElementById('output').innerText = data.message;
        });
}
