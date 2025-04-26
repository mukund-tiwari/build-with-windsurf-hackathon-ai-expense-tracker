// main.js: Handle Add Expense and Ask AI interactions
document.addEventListener('DOMContentLoaded', () => {
  // Elements
  const expText = document.getElementById('expense-text');
  const expBtn = document.getElementById('expense-submit');
  const expResult = document.getElementById('expense-result');

  const askText = document.getElementById('ask-text');
  const askBtn = document.getElementById('ask-submit');
  const askResult = document.getElementById('ask-result');

  // Add Expense event
  expBtn.addEventListener('click', async () => {
    const text = expText.value.trim();
    if (!text) {
      expResult.textContent = 'Please enter some text.';
      return;
    }
    expResult.textContent = 'Submitting...';
    try {
      const resp = await fetch('/api/expenses', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || JSON.stringify(data));
      expResult.textContent = JSON.stringify(data, null, 2);
      expText.value = '';
    } catch (err) {
      expResult.textContent = 'Error: ' + err.message;
    }
  });

  // Ask AI event
  askBtn.addEventListener('click', async () => {
    const text = askText.value.trim();
    if (!text) {
      askResult.textContent = 'Please enter some text.';
      return;
    }
    askResult.textContent = 'Submitting...';
    try {
      const resp = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || JSON.stringify(data));
      askResult.textContent = JSON.stringify(data, null, 2);
      askText.value = '';
    } catch (err) {
      askResult.textContent = 'Error: ' + err.message;
    }
  });
});