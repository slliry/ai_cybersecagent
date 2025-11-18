document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('threat-form');
  const input = document.getElementById('query');
  const result = document.getElementById('result');
  const chips = document.getElementById('chips');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = input.value.trim();
    if (!query) {
      render({ response: 'Введите вопрос по информационной безопасности.' });
      return;
    }
    try {
      setLoading(true);
      const resp = await fetch('/api/assistant', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });
      const data = await resp.json();
      render(data);
    } catch (err) {
      render({ response: 'Сеть недоступна или сервер не отвечает.' });
    } finally {
      setLoading(false);
    }
  });

  chips?.addEventListener('click', (e) => {
    if (e.target instanceof HTMLButtonElement && e.target.dataset.value) {
      input.value = e.target.dataset.value;
      input.focus();
    }
  });

  function render(data) {
    result.classList.remove('empty-state');
    result.innerHTML = '';

    if (data && Array.isArray(data.controls)) {
      const sections = [];

      if (data.summary || data.threat) {
        sections.push(createBlock('Кратко', [
          data.summary && `Суть: ${data.summary}`,
          data.threat && `Нормализованная угроза: ${data.threat}`
        ].filter(Boolean)));
      }

      if (data.controls?.length) {
        sections.push(createBlock('Контроли', data.controls));
      }

      const categories = data.control_categories || {};
      if (Object.keys(categories).length) {
        const formatted = Object.entries(categories).map(([k, arr]) => `${k}: ${arr.join(', ') || '—'}`);
        sections.push(createBlock('Категории контролей', formatted));
      }

      if (data.recommendations?.length) {
        sections.push(createBlock('Рекомендации', data.recommendations));
      }

      if (data.standards?.length) {
        sections.push(createBlock('Стандарты и нормы', data.standards));
      }

      if (!sections.length) {
        result.textContent = 'Ответ пуст.';
        return;
      }

      sections.forEach(section => result.appendChild(section));
    } else if (data && typeof data.response === 'string') {
      const msg = document.createElement('div');
      msg.className = 'result-block';
      msg.textContent = data.response;
      result.appendChild(msg);
      if (data.model_unavailable) {
        const hint = document.createElement('div');
        hint.className = 'result-block';
        hint.textContent = 'Добавьте GEMINI_API_KEY перед запуском приложения.';
        result.appendChild(hint);
      }
    } else {
      result.textContent = 'Ответ непонятен. Попробуйте снова.';
    }
  }

  function createBlock(title, listItems) {
    const block = document.createElement('div');
    block.className = 'result-block';
    const header = document.createElement('h4');
    header.textContent = title;
    block.appendChild(header);
    const list = document.createElement('ul');
    list.className = 'controls';
    listItems.forEach(item => {
      const li = document.createElement('li');
      li.textContent = item;
      list.appendChild(li);
    });
    block.appendChild(list);
    return block;
  }

  function setLoading(on) {
    const btn = form.querySelector('button');
    if (on) {
      btn.disabled = true;
      btn.dataset.prev = btn.textContent;
      btn.textContent = 'Обработка…';
      result.innerHTML = '<div class="spinner"></div>';
    } else {
      btn.disabled = false;
      if (btn.dataset.prev) btn.textContent = btn.dataset.prev;
    }
  }
});