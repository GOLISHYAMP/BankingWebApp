const loginForm = document.getElementById('login-form');
const registerForm = document.getElementById('register-form');
const balanceButton = document.getElementById('balance-button');
const balanceDisplay = document.getElementById('balance');
const depositForm = document.getElementById('deposit-form');
const withdrawForm = document.getElementById('withdraw-form');
const transferForm = document.getElementById('transfer-form');
const transactionsButton = document.getElementById('transactions-button');
const transactionsList = document.getElementById('transactions');

let token = '';

// Handle registration
registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('register-username').value;
    const password = document.getElementById('register-password').value;

    const res = await fetch('/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });
    const data = await res.json();
    alert(data.msg);
});

// Handle login
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;

    const res = await fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });
    const data = await res.json();
    if (data.access_token) {
        token = data.access_token;
        document.getElementById('login-register').style.display = 'none';
        document.getElementById('banking-operations').style.display = 'block';
    } else {
        alert(data.msg);
    }
});

// Handle balance check
balanceButton.addEventListener('click', async () => {
    const res = await fetch('/balance', {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await res.json();
    balanceDisplay.textContent = `Balance: $${data.balance}`;
});

// Handle deposit
depositForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const amount = document.getElementById('deposit-amount').value;

    const res = await fetch('/deposit', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ amount: parseFloat(amount) })
    });
    const data = await res.json();
    alert(data.msg);
    balanceButton.click(); // Refresh balance
});

// Handle withdrawal
withdrawForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const amount = document.getElementById('withdraw-amount').value;

    const res = await fetch('/withdraw', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ amount: parseFloat(amount) })
    });
    const data = await res.json();
    alert(data.msg);
    balanceButton.click(); // Refresh balance
});

// Handle transfer
transferForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const amount = document.getElementById('transfer-amount').value;
    const recipient = document.getElementById('recipient-username').value;

    const res = await fetch('/transfer', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ amount: parseFloat(amount), recipient })
    });
    const data = await res.json();
    alert(data.msg);
    balanceButton.click(); // Refresh balance
});

// Handle viewing transactions
transactionsButton.addEventListener('click', async () => {
    const res = await fetch('/transactions', {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await res.json();
    transactionsList.innerHTML = '';
    data.transactions.forEach(tx => {
        const li = document.createElement('li');
        li.textContent = `${tx.type}: $${tx.amount} - ${tx.description} (${tx.timestamp})`;
        transactionsList.appendChild(li);
    });
});
