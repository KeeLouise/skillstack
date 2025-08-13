// Helper functions - KR 13/08/2025
function $(sel, ctx) { return (ctx || document).querySelector(sel); } // Selects first element on the page that matches the CSS selector given.
function $all(sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); } // Selects all matching elements and returns them as an array.
function on(el, ev, fn, opts) { if (el) el.addEventListener(ev, fn, opts || false); } // Adds event listener.
function formatBytes(bytes) {                                                       // Takes a file size in bytes and turns it into mb, gb or tb.
  if (!Number.isFinite(bytes)) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let i = 0, v = bytes;
  while (v >= 1024 && i < units.length - 1) { v /= 1024; i++; }
  return v.toFixed(v >= 10 || i === 0 ? 0 : 1) + ' ' + units[i];
}

// Drag & drop upload - KR 13/08/2025
(function uploadEnhancements() { // Looks for the upload form. Script stops running if it doesn't exist.
  const form = document.querySelector('form[action*="attachments/upload"]');
  if (!form) return;

  const dz = $('.upload-dropzone', form) || form;       
  const fileInput = $('input[type="file"]', form);      
  if (!fileInput) return;

  if (!dz.hasAttribute('tabindex')) dz.setAttribute('tabindex', '0');
  on(dz, 'keydown', (e) => {
    if (e.key === ' ' || e.key === 'Enter') {
      e.preventDefault();
      fileInput.click();
    }
  });

  // Create live file list under the dropzone - KR 13/08/2025
  const list = document.createElement('div');
  list.className = 'upload-file-list small text-muted';
  dz.insertAdjacentElement('afterend', list); // Creates section after dropzone to show the selected file & total size.

  function renderList(files) { // Displays file name & its size. Also shows total size at the bottom. This is called whenever the file changes.
    if (!files || !files.length) {
      list.innerHTML = '';
      return;
    }
    let total = 0;
    let html = '<ul class="mb-1">';
    Array.from(files).forEach(f => {
      total += f.size || 0;
      html += `<li class="text-truncate">${f.name} <span class="text-secondary">(${formatBytes(f.size || 0)})</span></li>`;
    });
    html += '</ul>';
    html += `<div class="text-secondary">Total: <strong>${formatBytes(total)}</strong></div>`;
    list.innerHTML = html;
  }

  on(fileInput, 'change', e => renderList(e.target.files)); // When files are picked through the standard input, they will render on the list.

  // Drag & drop styling
  ['dragenter', 'dragover'].forEach(ev => on(dz, ev, (e) => {
    e.preventDefault(); e.stopPropagation();
    dz.classList.add('is-dragging');
  }));
  ['dragleave', 'dragend', 'drop'].forEach(ev => on(dz, ev, (e) => {
    e.preventDefault(); e.stopPropagation();
    dz.classList.remove('is-dragging');
  })); // Adds/removes a CSS class while dragging files over dropzone and prevents browser from opening the file if dropped.

  on(dz, 'drop', (e) => { // When dropped, files are put into the real input. A change event is then triggered so the list updates.
    const dt = e.dataTransfer;
    if (!dt || !dt.files || !dt.files.length) return;

    try {
      fileInput.files = dt.files;
    } catch (_) {
      try {
        const buf = new DataTransfer();
        Array.from(dt.files).forEach(f => buf.items.add(f));
        fileInput.files = buf.files;
      } catch (_) {
        alert('Your browser blocked dropping files here. Please click to select files instead.');
        return;
      }
    }

    const evt = new Event('change', { bubbles: true });
    fileInput.dispatchEvent(evt);
  });

  // Status dropdown AJAX - KR 13/08/2025
(function () {
  const dropdown = document.getElementById('statusDropdown');
  const saveMsg = document.getElementById('statusSaveMsg');
  const badge   = document.getElementById('project-status-badge');
  if (!dropdown) return;

  // Read the endpoint straight from the DOM to avoid undefined IDs
  const updateUrl = dropdown.getAttribute('data-update-url');

  // Robust CSRF getter (works even if the hidden input isn't present)
  function getCsrf() {
    const inp = document.querySelector('input[name=csrfmiddlewaretoken]');
    if (inp && inp.value) return inp.value;
    const m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : '';
  }

  function showMsg(text, success = true) {
    if (!saveMsg) return;
    saveMsg.textContent = text;
    saveMsg.className = `small ms-2 ${success ? 'text-success' : 'text-danger'}`;
    setTimeout(() => { saveMsg.textContent = ''; }, 3000);
  }

  function updateBadge(val) {
    if (!badge) return;
    // reset classes
    badge.className = 'badge project-status-badge';
    if (val === 'completed') {
      badge.classList.add('bg-success');
      badge.textContent = 'Completed';
    } else if (val === 'ongoing') {
      badge.classList.add('bg-warning', 'text-dark');
      badge.textContent = 'Ongoing';
    } else if (val === 'paused') {
      badge.classList.add('bg-danger');
      badge.textContent = 'Paused';
    } else {
      badge.classList.add('text-bg-light', 'border');
      badge.textContent = 'Unknown';
    }
  }

  dropdown.addEventListener('change', () => {
    const status = dropdown.value;
    if (!status || !updateUrl) return;

    updateBadge(status);

    fetch(updateUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': getCsrf()
      },
      body: JSON.stringify({ status })
    })
    .then(res => res.json().catch(() => ({})).then(data => ({ ok: res.ok, data })))
    .then(({ ok, data }) => {
      if (ok && data && data.success) {
        showMsg('Status updated');
      } else {
        showMsg(data && data.error ? data.error : 'Error updating status', false);
        updateBadge(dropdown.getAttribute('data-current') || '');
      }
    })
    .catch(() => {
      showMsg('Error updating status', false);
      updateBadge(dropdown.getAttribute('data-current') || '');
    });
  });
})();

  // Pre-submission checks
  on(form, 'submit', (e) => {
    const files = fileInput.files || [];
    if (!files.length) return;

    const MAX_FILES = 20;
    const MAX_FILE_MB = 50;
    const MAX_TOTAL_MB = 500;
    const overs = [];
    let totalSize = 0;

    Array.from(files).forEach((f) => {
      totalSize += f.size || 0;
      if (f.size > MAX_FILE_MB * 1024 * 1024) overs.push(f.name);
    });

    if (files.length > MAX_FILES) {
      e.preventDefault();
      alert(`Too many files selected (max ${MAX_FILES}).`);
      return;
    }
    if (overs.length) {
      e.preventDefault();
      alert(`These files exceed ${MAX_FILE_MB}MB:\n- ${overs.join('\n- ')}`);
      return;
    }
    if (totalSize > MAX_TOTAL_MB * 1024 * 1024) {
      e.preventDefault();
      alert(`Total upload size exceeds ${MAX_TOTAL_MB}MB.`);
      return;
    }
  });
})();