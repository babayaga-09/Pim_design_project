/**
 * Checks if a session token exists. If not, it redirects the user to the login page.
 * @param {string} token - The session token from localStorage.
 * @returns {boolean} - True if the user is authenticated, false otherwise.
 */
function guard(token) {
  if (!token) {
    window.location.href = '/';
    return false;
  }
  return true;
}

/**
 * Gets a specific parameter's value from the current page's URL.
 * @param {string} name - The name of the URL parameter to get.
 * @returns {string | null} - The value of the parameter or null if not found.
 */
function getURLParameter(name) {
  const params = new URLSearchParams(window.location.search);
  return params.get(name);
}

/**
 * Fetches the data for a single particle from the API.
 * @param {string} particleId - The ID of the particle to fetch.
 * @param {string} token - The user's session token.
 * @returns {Promise<object|null>} - A promise that resolves to the particle object or null.
 */
async function fetchParticleById(particleId, token) {
  const response = await fetch(`/particles/${particleId}?session=${token}`);
  if (!response.ok) {
    alert('Could not fetch particle data.');
    return null;
  }
  return await response.json();
}

/**
 * Makes a POST request to a given endpoint.
 * @param {string} endpoint - The API endpoint to call.
 * @param {object} bodyObject - The JavaScript object to send as the request body.
 * @param {function} successAction - The callback function to execute on a successful response.
 */
async function postrequest(endpoint, bodyObject, successAction) {
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(bodyObject),
  });

  if (response.ok) {
    const data = await response.json();
    successAction(data);
  } else {
    alert('Request failed. Please check your inputs or session.');
  }
}

/**
 A specific callback for the login function to store the session and redirect.
 * @param {object} data - The response data from the login API call.
 */
function storeSessionInfo(data) {
  localStorage.setItem('pim_session', data.session);
  window.location.href = '/index.html';
}

//Attaches logout functionality to any logout buttons on the page.
function initializeLogoutButtons() {
  const token = localStorage.getItem('pim_session');
  const logoutButtons = document.querySelectorAll('a[href="login.html"]');

  logoutButtons.forEach(button => {
    button.addEventListener('click', async (event) => {
      event.preventDefault();

      if (token) {
        // Call the backend to invalidate the session
        await fetch('/logout', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session: token }),
        });
        localStorage.removeItem('pim_session');
        alert('You have been logged out.');
      }
      
      window.location.href = '/';
    });
  });
}

// Run the global initializers once the DOM is ready.
document.addEventListener('DOMContentLoaded', () => {
  initializeLogoutButtons();
});
