function initializeLoginPage() {
  const loginForm = document.querySelector('.form--auth');
  
  loginForm.addEventListener('submit', (event) => {
    event.preventDefault();
    const username = loginForm.querySelector('input[name="username"]').value;
    const password = loginForm.querySelector('input[name="password"]').value;

    postrequest('/login', { username, password }, storeSessionInfo);
  });
}

// Run the initializer for this page.
initializeLoginPage();