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
    document.querySelector('.viewer__head .idchip').textContent = `#${particle.user_facing_id}`;
    document.querySelector('.viewer__head .badge').textContent = new Date(particle.created_at).toLocaleDateString();
    document.querySelector('h2').textContent = particle.title;
    
    // Add the ql-editor class for Quill's styles to apply
    const articleViewer = document.querySelector('article.viewer');
    articleViewer.classList.add('ql-editor');
    articleViewer.innerHTML = particle.body;

    document.querySelector('.viewer__head a.btn--success').href = `/editor.html?id=${particle.id}`;
  }
}

// Get the session token and run the initializer for this page.
const token = localStorage.getItem('pim_session');
initializeViewerPage(token);
