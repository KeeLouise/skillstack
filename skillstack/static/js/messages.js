(function () {
  var pageBadge = document.getElementById('page-unread-badge');
  var inboxBadge = document.getElementById('inbox-unread-badge');
  var unreadUrl =
    (inboxBadge && inboxBadge.dataset.unreadUrl) ||
    (pageBadge && pageBadge.dataset.unreadUrl) ||
    '';

  function setBadge(el, n) {
    if (!el) return;
    n = Number(n) || 0;
    if (n > 0) {
      el.textContent = n;
      el.style.display = '';
    } else {
      el.textContent = '';
      el.style.display = 'none';
    }
  }

  async function refreshUnread() {
    if (!unreadUrl) return;
    try {
      var res = await fetch(unreadUrl, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        credentials: 'same-origin',
      });
      if (!res.ok) return;
      var data = await res.json();
      var n = Number(data.unread || 0);
      setBadge(pageBadge, n);
      setBadge(inboxBadge, n);
    } catch (e) {
      if (window.DEBUG) console.debug(e);
    }
  }

  if (unreadUrl) {
    refreshUnread();
    setInterval(refreshUnread, 30000);
  }

  document.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'visible') {
      refreshUnread();
    }
  });

  function getCsrf() {
    var m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : '';
  }

  var cards = document.querySelectorAll('[data-msg-id]');
  cards.forEach(function (card) {
    card.addEventListener('click', function (e) {
      // Ignore clicks on delete/archive buttons or anything with data-no-card-click - KR 11/08/2025
      if (
        e.target.closest('form') || 
        e.target.closest('button') || 
        e.target.closest('[data-no-card-click]')
      ) {
        return;
      }

      var url = card.getAttribute('data-mark-read-url') || '';
      var id = card.getAttribute('data-msg-id');
      if (!url || !id) return;

      try {
        fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCsrf(),
          },
          body: JSON.stringify({ id: id }),
          credentials: 'same-origin',
        }).catch(function (e) {
          if (window.DEBUG) console.debug(e);
        });
      } catch (e) {
        if (window.DEBUG) console.debug(e);
      }
    });
  });

  // --- Auto-dismiss Bootstrap alerts after 4s ---
  function autoDismissAlerts() {
    var alerts = document.querySelectorAll('.alert');
    alerts.forEach(function (el) {
      setTimeout(function () {
        try {
          var inst = bootstrap.Alert.getOrCreateInstance(el);
          inst.close();
        } catch (e) {
          /* ignore */
        }
      }, 4000);
    });
  }
  autoDismissAlerts();

  window.addEventListener('pageshow', function (e) {
    if (e.persisted) {
      refreshUnread();
      autoDismissAlerts();
    }
  });
})();

// attachment dropzone + live list (partially reused from projects.js- KR 13/08/2025

(function composeAttachments() {
  const form = document.querySelector('.container form[enctype="multipart/form-data"]');
  if (!form) return;

  const fileInput = form.querySelector('input[type="file"]');
  if (!fileInput) return;

  const MAX_FILES = 10;
  const MAX_FILE_MB = 25;
  const MAX_TOTAL_MB = 100;

  function formatBytes(bytes) {
    if (!Number.isFinite(bytes)) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let i = 0, v = bytes;
    while (v >= 1024 && i < units.length - 1) { v /= 1024; i++; }
    return v.toFixed(v >= 10 || i === 0 ? 0 : 1) + ' ' + units[i];
  }

  const dropzone = document.createElement('div');
  dropzone.className = 'msg-dropzone';
  dropzone.setAttribute('role', 'button');
  dropzone.setAttribute('tabindex', '0');
  dropzone.setAttribute('aria-label', 'Add attachments: drop files here or press Enter/Space to select');

  dropzone.innerHTML = `
    <div class="dz-inner">
      <div class="dz-icon" aria-hidden="true">📎</div>
      <div class="dz-text">
        <strong>Drop files here</strong> or <span class="dz-action">click to select</span>
        <div class="dz-sub">Up to ${MAX_FILES} files, ${MAX_FILE_MB}MB each, max ${MAX_TOTAL_MB}MB total</div>
      </div>
    </div>
  `;

  const listWrap = document.createElement('div');
  listWrap.className = 'msg-file-list';

  fileInput.insertAdjacentElement('afterend', dropzone);
  dropzone.insertAdjacentElement('afterend', listWrap);

  dropzone.addEventListener('click', () => fileInput.click());
  dropzone.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      fileInput.click();
    }
  });

  ['dragenter', 'dragover'].forEach(ev =>
    dropzone.addEventListener(ev, (e) => {
      e.preventDefault(); e.stopPropagation();
      dropzone.classList.add('is-dragging');
    })
  );
  ['dragleave', 'dragend', 'drop'].forEach(ev =>
    dropzone.addEventListener(ev, (e) => {
      e.preventDefault(); e.stopPropagation();
      dropzone.classList.remove('is-dragging');
    })
  );

  dropzone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    if (!dt || !dt.files || !dt.files.length) return;

    try {
      fileInput.files = dt.files;
    } catch {
      const buf = new DataTransfer();
      Array.from(dt.files).forEach(f => buf.items.add(f));
      fileInput.files = buf.files;
    }

    renderList(fileInput.files);
  });

  fileInput.addEventListener('change', (e) => {
    renderList(e.target.files);
  });

  function renderList(files) {
    listWrap.innerHTML = '';
    if (!files || !files.length) return;

    const ul = document.createElement('ul');
    ul.className = 'msg-file-ul';
    let totalSize = 0;

    Array.from(files).forEach((f, idx) => {
      totalSize += f.size || 0;

      const li = document.createElement('li');
      li.className = 'msg-file-li';

      const chip = document.createElement('span');
      chip.className = 'msg-file-chip';
      chip.title = f.name;

      chip.innerHTML = `
        <span class="chip-name text-truncate">${f.name}</span>
        <span class="chip-size">${formatBytes(f.size || 0)}</span>
        <button type="button" class="chip-remove" aria-label="Remove ${f.name}">&times;</button>
      `;

      chip.querySelector('.chip-remove').addEventListener('click', () => {
        const buf = new DataTransfer();
        Array.from(fileInput.files).forEach((file, i) => {
          if (i !== idx) buf.items.add(file);
        });
        fileInput.files = buf.files;
        renderList(fileInput.files);
      });

      li.appendChild(chip);
      ul.appendChild(li);
    });

    const total = document.createElement('div');
    total.className = 'msg-file-total text-muted';
    total.textContent = `Total: ${formatBytes(totalSize)}`;

    listWrap.appendChild(ul);
    listWrap.appendChild(total);
  }

  form.addEventListener('submit', (e) => {
    const files = fileInput.files || [];
    if (!files.length) return;

    let totalSize = 0;
    const oversized = [];
    const seen = new Set(); // prevent duplicates by name+size signature

    for (const f of files) {
      totalSize += f.size || 0;
      if (f.size > MAX_FILE_MB * 1024 * 1024) oversized.push(f.name);
      const sig = `${f.name}__${f.size}`;
      if (seen.has(sig)) {
        e.preventDefault();
        alert(`Duplicate file detected: ${f.name}`);
        return;
      }
      seen.add(sig);
    }

    if (files.length > MAX_FILES) {
      e.preventDefault();
      alert(`Too many files selected (max ${MAX_FILES}).`);
      return;
    }
    if (oversized.length) {
      e.preventDefault();
      alert(`These files exceed ${MAX_FILE_MB}MB:\n- ${oversized.join('\n- ')}`);
      return;
    }
    if (totalSize > MAX_TOTAL_MB * 1024 * 1024) {
      e.preventDefault();
      alert(`Total upload size exceeds ${MAX_TOTAL_MB}MB.`);
    }
  });
})();