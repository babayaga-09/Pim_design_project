/**
 * Applies the selected theme by setting a data-theme attribute on the root <html> element.
 * @param {string} theme - The theme to apply ('light' or 'dark').
 */
function applyTheme(theme) {
  if (theme === 'light') {
    document.documentElement.setAttribute('data-theme', 'light');
  } else {
    // Default to dark theme if the value is anything else or not set
    document.documentElement.removeAttribute('data-theme');
  }
}

/**
 * Initializes the settings page functionality.
 * @param {string} token - The user's session token.
 */
function initializeSettingsPage(token) {
  if (!guard(token)) return; // from common.js

  const themeSelect = document.getElementById('theme-select');
  const exportButton = document.getElementById('export-button');

  // Theme Switch

  // 1. On page load, apply the saved theme from localStorage
  const savedTheme = localStorage.getItem('pim_theme') || 'dark';
  applyTheme(savedTheme);
  themeSelect.value = savedTheme;

  themeSelect.addEventListener('change', () => {
    const selectedTheme = themeSelect.value;
    localStorage.setItem('pim_theme', selectedTheme);
    applyTheme(selectedTheme);
  });

  // Export Data 
  exportButton.addEventListener('click', async () => {
    try {
      exportButton.textContent = 'Exporting...';
      exportButton.disabled = true;

      const response = await fetch(`/export?session=${token}`);

      if (!response.ok) {
        throw new Error('Failed to fetch data for export.');
      }

      const dataBlob = await response.blob();
      const url = window.URL.createObjectURL(dataBlob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = 'pim_export.json';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();

    } catch (error) {
      console.error('Export failed:', error);
      alert('Could not export data. Please try again.');
    } finally {
      exportButton.textContent = 'Export All to JSON';
      exportButton.disabled = false;
    }
  });
}

// to prevent a flash of incorrect theme.
applyTheme(localStorage.getItem('pim_theme') || 'dark');

document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('pim_session');
    initializeSettingsPage(token);
});
