function initializeSearchPage(token) {
  // This helper function is from common.js
  if (!guard(token)) return;

  const searchForm = document.querySelector('.searchbar');
  const searchInput = searchForm.querySelector('.input');
  const createButton = searchForm.querySelector('a.btn');

  const displayParticles = async (query = '') => {
    const response = await fetch(`/search?q=${encodeURIComponent(query)}&session=${token}`);
    if (!response.ok) {
      alert('Session expired. Please log in again.');
      localStorage.removeItem('pim_session');
      window.location.href = '/';
      return;
    }
    
    const particles = await response.json();
    const tableBody = document.querySelector('.table tbody');
    tableBody.innerHTML = ''; // Clear existing results
    particles.forEach(p => {
      const row = document.createElement('tr');
      const formattedDate = new Date(p.created_at).toLocaleDateString();
      row.innerHTML = `
        <td>#${p.user_facing_id}</td>
        <td>${formattedDate}</td>
        <td class="table__title">${p.title}</td>
        <td class="table__actions">
          <a class="btn btn--success" href="/viewer.html?id=${p.id}">View</a>
          <a class="btn" href="/editor.html?id=${p.id}">Edit</a>
        </td>
      `;
      tableBody.appendChild(row);
    });
  };

  searchForm.addEventListener('submit', (e) => {
    e.preventDefault();
    displayParticles(searchInput.value);
  });

  createButton.addEventListener('click', (e) => {
    e.preventDefault();
    const newTitle = searchInput.value.trim();
    if (!newTitle) {
      alert('Please type a title before creating.');
      return;
    }
    window.location.href = `/editor.html?title=${encodeURIComponent(newTitle)}`;
  });

  // Initial load of all particles
  displayParticles();
}

const token = localStorage.getItem('pim_session');
initializeSearchPage(token);
