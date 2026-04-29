/**
 * ajax_toggle.js
 * Handles attendance toggling via AJAX (fetch API) — no page reload.
 * Called from admin_dashboard.html.
 */

/**
 * Toggle attendance for a participant.
 * @param {number} participantId  - Django PK of the Participant
 * @param {HTMLButtonElement} btn - The button element that was clicked
 */
function toggleAttendance(participantId, btn) {
  // Get CSRF token from the cookie
  const csrfToken = getCookie('csrftoken');

  // Disable button while request is in flight
  btn.disabled = true;
  const originalContent = btn.innerHTML;
  btn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status"></span>`;

  fetch(`/toggle-attendance/${participantId}/`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': csrfToken,
      'Content-Type': 'application/json',
      'X-Requested-With': 'XMLHttpRequest',
    },
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      if (data.success) {
        updateAttendanceButton(btn, data.attendance);
        showToast(data.message, data.attendance ? 'success' : 'warning');
      } else {
        btn.innerHTML = originalContent;
        btn.disabled = false;
        showToast('Failed to update attendance. Please try again.', 'danger');
      }
    })
    .catch((err) => {
      console.error('Attendance toggle error:', err);
      btn.innerHTML = originalContent;
      btn.disabled = false;
      showToast('Network error. Please check your connection.', 'danger');
    });
}

/**
 * Update the button appearance based on the new attendance state.
 * @param {HTMLButtonElement} btn   - The toggle button
 * @param {boolean} attended        - New attendance state
 */
function updateAttendanceButton(btn, attended) {
  btn.disabled = false;

  if (attended) {
    btn.className = 'btn attendance-btn btn-success';
    btn.innerHTML = `<i class="bi bi-check-circle-fill me-1"></i>Present`;
  } else {
    btn.className = 'btn attendance-btn btn-outline-secondary';
    btn.innerHTML = `<i class="bi bi-circle me-1"></i>Absent`;
  }
}

/**
 * Show a transient Bootstrap toast notification.
 * @param {string} message  - Message to display
 * @param {string} type     - Bootstrap color: success | warning | danger | info
 */
function showToast(message, type = 'info') {
  // Create toast container if it doesn't exist
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'position-fixed bottom-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
  }

  const toastId = `toast-${Date.now()}`;
  const iconMap = {
    success: 'bi-check-circle-fill',
    warning: 'bi-exclamation-triangle-fill',
    danger:  'bi-x-circle-fill',
    info:    'bi-info-circle-fill',
  };
  const icon = iconMap[type] || 'bi-info-circle-fill';

  const toastEl = document.createElement('div');
  toastEl.id = toastId;
  toastEl.className = `toast align-items-center text-bg-${type} border-0`;
  toastEl.setAttribute('role', 'alert');
  toastEl.setAttribute('aria-live', 'assertive');
  toastEl.setAttribute('aria-atomic', 'true');
  toastEl.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">
        <i class="bi ${icon} me-2"></i>${message}
      </div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto"
              data-bs-dismiss="toast" aria-label="Close"></button>
    </div>`;

  container.appendChild(toastEl);

  // Initialize and show via Bootstrap Toast API
  const bsToast = new bootstrap.Toast(toastEl, { delay: 3500 });
  bsToast.show();

  // Clean up DOM after hidden
  toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}

/**
 * Read a cookie value by name.
 * Used to retrieve the Django CSRF token.
 * @param {string} name - Cookie name
 * @returns {string|null}
 */
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
      cookie = cookie.trim();
      if (cookie.startsWith(name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
