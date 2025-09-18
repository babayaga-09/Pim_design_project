/**
 * Initializes the login page functionality.
 * * This function selects the login form and adds an event listener for the 'submit' event.
 * It prevents the default form submission, retrieves the username and password from the form inputs,
 * and sends them to the server using a POST request.
 * * @function
 * @returns {void}
 */
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
