// main.js: Handle Add Expense and Ask AI interactions
document.addEventListener('DOMContentLoaded', () => {
  const chatWindow = document.getElementById('chat-window');
  const chatInput = document.getElementById('chat-input');
  const chatSend = document.getElementById('chat-send');

  function appendMessage(sender, text) {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message', sender);
    msgDiv.textContent = text;
    chatWindow.appendChild(msgDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;
  }

  chatSend.addEventListener('click', async () => {
    const text = chatInput.value.trim();
    if (!text) return;
    appendMessage('user', text);
    chatInput.value = '';
    appendMessage('status', 'Sending...');
    try {
      const resp = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });
      const data = await resp.json();
      // Remove status message
      const last = chatWindow.querySelector('.status:last-child');
      if (last) chatWindow.removeChild(last);
      if (!resp.ok) {
        appendMessage('assistant', 'Error: ' + (data.detail || JSON.stringify(data)));
        return;
      }
      // Interpret response
      if (data.action === 'parse_expense' && data.expense) {
        const e = data.expense;
        appendMessage('assistant',
          `Expense recorded: ₹${e.amount} on ${e.timestamp} for ${e.description}` +
          (e.category ? ` (category: ${e.category})` : '')
        );
      } else if (data.action === 'query_expenses' && data.expenses) {
        if (data.expenses.length === 0) {
          appendMessage('assistant', 'No expenses found for that query.');
        } else {
          appendMessage('assistant', 'Expenses:');
          data.expenses.forEach(e => {
            appendMessage('assistant',
              `- ₹${e.amount} on ${e.timestamp}: ${e.description}` +
              (e.category ? ` (cat: ${e.category})` : '')
            );
          });
        }
      } else if (data.action === 'summarize_expenses' && data.summary) {
        const s = data.summary;
        appendMessage('assistant', `Total: ₹${s.total}`);
        if (s.breakdown && s.breakdown.length) {
          appendMessage('assistant', 'Breakdown:');
          s.breakdown.forEach(b => {
            appendMessage('assistant', `- ${b.period}: ₹${b.total}`);
          });
      } else if (data.action === 'get_last_expense' && data.expense) {
        const e = data.expense;
        let msg = `Last expense: ₹${e.amount} on ${e.timestamp} for ${e.description}`;
        if (e.participants && e.participants.length) {
          msg += ` (participants: ${e.participants.join(', ')})`;
        }
        appendMessage('assistant', msg);
      } else if (data.action === 'split_expense' && data.split) {
        const s = data.split;
        appendMessage('assistant', `Share for ${s.participant}: ₹${s.share.toFixed(2)}`);
        }
      } else if (data.response) {
        appendMessage('assistant', data.response);
      } else {
        appendMessage('assistant', JSON.stringify(data));
      }
    } catch (err) {
      appendMessage('assistant', 'Error: ' + err.message);
    }
  });
});