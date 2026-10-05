* {
  box-sizing: border-box;
}

:root {
  --bg: #f4f7fb;
  --panel: #ffffff;
  --primary: #2457f5;
  --primary-dark: #173fc8;
  --success: #17a673;
  --danger: #d9534f;
  --text: #1f2a37;
  --muted: #667085;
  --border: #e5e7eb;
  --shadow: 0 10px 25px rgba(36, 87, 245, 0.08);
}

body {
  margin: 0;
  font-family: Arial, Helvetica, sans-serif;
  background: var(--bg);
  color: var(--text);
}

.auth-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, #eef4ff 0%, #f7f7ff 100%);
}

.auth-box {
  width: min(440px, 90vw);
  background: var(--panel);
  border-radius: 20px;
  box-shadow: var(--shadow);
  padding: 32px;
}

.brand {
  text-align: center;
  margin-bottom: 20px;
}

.brand h1 {
  margin: 0;
  color: var(--primary);
}

.brand p {
  margin: 8px 0 0;
  color: var(--muted);
}

.auth-form,
.transaction-form,
.chat-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

label {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-weight: 600;
  color: var(--text);
}

input,
select,
button {
  border-radius: 12px;
  border: 1px solid var(--border);
  font: inherit;
}

input,
select {
  padding: 12px 14px;
  background: #fff;
}

button {
  background: var(--primary);
  color: white;
  padding: 12px 16px;
  cursor: pointer;
  font-weight: 700;
  transition: background 0.2s ease;
}

button:hover {
  background: var(--primary-dark);
}

.auth-footer {
  margin-top: 18px;
  text-align: center;
  color: var(--muted);
}

.auth-footer a {
  color: var(--primary);
  font-weight: 700;
  text-decoration: none;
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 5vw;
  background: #fff;
  border-bottom: 1px solid var(--border);
}

.user-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-actions a {
  color: var(--primary);
  text-decoration: none;
  font-weight: 700;
}

.dashboard-shell {
  width: min(1200px, 90vw);
  margin: 32px auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(180px, 1fr));
  gap: 20px;
}

.card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 22px;
  box-shadow: var(--shadow);
}

.summary-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.summary-card .label {
  color: var(--muted);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.75rem;
}

.summary-card strong {
  font-size: 2rem;
}

.summary-card.income strong {
  color: var(--success);
}

.summary-card.expense strong {
  color: var(--danger);
}

.summary-card.balance strong {
  color: var(--primary);
}

.content-grid {
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: 24px;
}

.grid.two-cols {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.transaction-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.transaction-list li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border);
  padding-bottom: 10px;
}

.transaction-list .meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.transaction-list .amount {
  font-weight: 700;
}

.transaction-list .amount.income {
  color: var(--success);
}

.transaction-list .amount.expense {
  color: var(--danger);
}

.assistant-card {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.chat-messages {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 240px;
  overflow-y: auto;
  padding-right: 6px;
}

.bubble {
  max-width: 80%;
  padding: 12px 14px;
  border-radius: 16px;
  line-height: 1.5;
}

.bubble.assistant {
  background: #edf2ff;
  color: var(--text);
  align-self: flex-start;
}

.bubble.user {
  background: var(--primary);
  color: white;
  align-self: flex-end;
}

.chat-form {
  flex-direction: row;
  align-items: center;
}

.chat-form input {
  flex: 1;
}

@media (max-width: 800px) {
  .content-grid,
  .summary-grid,
  .grid.two-cols {
    grid-template-columns: 1fr;
  }

  .chat-form {
    flex-direction: column;
  }
}
