async function initializeViewerPage(token) {
  // These helper functions are from common.js
  if (!guard(token)) return;
  
  const particleId = getURLParameter('id');
  if (!particleId) {
    alert('No particle ID specified.');
    window.location.href = '/index.html';
    return;
  }

  const particle = await fetchParticleById(particleId, token);
  if (particle) {
    document.title = `PIM labs — ${particle.title}`;
    document.getElementById('particle-title').textContent = particle.title;
    document.getElementById('particle-id').textContent = `#${particle.user_facing_id}`;
    document.getElementById('particle-date').textContent = new Date(particle.created_at).toLocaleDateString();
    document.getElementById('edit-button').href = `/editor.html?id=${particle.id}`;
    
    // The ql-editor class for Quill's styles to apply
    const articleViewer = document.querySelector('article.viewer');
    articleViewer.classList.add('ql-editor');
    articleViewer.innerHTML = particle.body;

  }
}

// Get the session token and run the initializer for this page.
const token = localStorage.getItem('pim_session');
initializeViewerPage(token);
