/**
 * Initializes the registration page functionality.
 * This function adds a 'submit' event listener to the registration form.
 * It prevents the default form submission, validates the inputs, and sends a POST request to the '/register' endpoint.
 * On success, it alerts the user and redirects to the login page.
 * On failure, it alerts the user with the error message from the server.
 * * @function
 * @returns {void}
 */
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
