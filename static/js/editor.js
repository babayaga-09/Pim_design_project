/**
 * Initializes the particle editor page. It handles loading existing particles or setting up a new one.
 * @param {string} token - The user's session token.
 */
async function initializeEditorPage(token) {
  // These helper functions are from common.js
  if (!guard(token)) return;

  const particleId = getURLParameter('id');
  const newTitle = getURLParameter('title');

  const titleInput = document.querySelector('.input[maxlength="140"]');
  const saveButton = document.querySelector('.btn--success');
  const deleteButton = document.getElementById('delete-button'); // Get the delete button

  const quill = new Quill('#editor', {
    modules: {
      toolbar: '#toolbar'
    },
    theme: 'snow'
  });

  if (particleId) {
    // Editing an existing particle
    const particle = await fetchParticleById(particleId, token);
    if (particle) {
      titleInput.value = particle.title;
      quill.root.innerHTML = particle.body;
      document.querySelector('.idchip').textContent = `#${particle.user_facing_id}`;
      deleteButton.style.display = 'inline-flex'; // Show the delete button
    }
  } else if (newTitle) {
    // Creating a new particle
    titleInput.value = newTitle;
    document.querySelector('.idchip').textContent = '#new';
  }

  saveButton.addEventListener('click', async () => {
    const title = titleInput.value;
    const body = quill.root.innerHTML;

    // Prevent saving a blank particle
    if (!title.trim() || quill.getLength() <= 1) {
      alert('Title and body cannot be empty.');
      return;
    }

    let response;
    if (particleId) {
      // to update an existing particle
      response = await fetch(`/particles/${particleId}?session=${token}`,  {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: title, body: body }),
      });

    } else {
      // to create a new particle
      response = await fetch(`/particles?session=${token}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, body, tags: [] }),
      });
    }

    if (response.ok) {
      const savedParticle = await response.json();
      alert('Particle saved!');
      window.location.href = `/viewer.html?id=${savedParticle.id}`;
    } else {
      alert('Failed to save particle.');
    }
  });

  deleteButton.addEventListener('click', async () => {
    const isConfirmed = confirm('Are you sure you want to delete this particle?');

    if (isConfirmed) {
      const response = await fetch(`/particles/${particleId}?session=${token}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        alert('Particle deleted!');
        window.location.href = '/index.html'; // Redirect to the main page
      } else {
        alert('Failed to delete particle.');
      }
    }
    // If user clicks "No", do nothing
  });
}

// Get the session token and run the initializer for this page.
const token = localStorage.getItem('pim_session');
initializeEditorPage(token);
