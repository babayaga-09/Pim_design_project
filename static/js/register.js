function initializeRegisterPage() {
  const registerForm = document.getElementById('register-form');
  
  registerForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const username = registerForm.querySelector('input[name="username"]').value;
    const password = registerForm.querySelector('input[name="password"]').value;

    if (!username || !password) {
      alert('Username and password cannot be empty.');
      return;
    }

    const response = await fetch('/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });

    if (response.ok) {
      alert('Registration successful! Please sign in.');
      window.location.href = '/'; // Redirect to login page
    } else {
      const errorData = await response.json();
      alert(`Registration failed: ${errorData.detail}`);
    }
  });
}

initializeRegisterPage();
