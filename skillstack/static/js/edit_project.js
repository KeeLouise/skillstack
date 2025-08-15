// Helpers - KR 13/08/2025
document.addEventListener('DOMContentLoaded', function () {
function $(sel, ctx) { return (ctx || document).querySelector(sel); }
function $all(sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); }
function on(el, ev, fn, opts) { if (el) el.addEventListener(ev, fn, opts || false); }
function debounce(fn, wait) { let t; return function () { clearTimeout(t); t = setTimeout(() => fn.apply(this, arguments), wait); }; }

// Field selectors (crispy renders real inputs; target by name) - KR 13/08/2025
(function () {
  const form = document.getElementById('editProjectForm');
  if (!form) return;

  const titleInput       = form.querySelector('[name="title"]');
  const descInput        = form.querySelector('[name="description"]');
  const startInput       = form.querySelector('[name="start_date"]');
  const endInput         = form.querySelector('[name="end_date"]');
  const statusSelect     = form.querySelector('[name="status"]');
  const inviteInput      = form.querySelector('[name="invite_emails"]');
  const submitButtons    = $all('button[type="submit"][form="editProjectForm"], #editProjectForm button[type="submit"]'});

  // Unsaved changes guard - KR 13/08/2025
  const initialData = new FormData(form);
  let isDirty = false;
  function checkDirty() {
    const now = new FormData(form);
    for (const [k, v] of now.entries()) {
      if (initialData.get(k) !== v) { isDirty = true; return; }
    }
    isDirty = false;
  }
  on(form, 'input', debounce(checkDirty, 150));
  on(window, 'beforeunload', function (e) {
    if (!isDirty) return;
    e.preventDefault();
    e.returnValue = '';
  });

  // Double-submit protection - KR 13/08/2025
  on(form, 'submit', function (e) {
    // run validation first
    if (!validateDates()) {
      e.preventDefault();
      return;
    }
    submitButtons.forEach(btn => {
      btn.disabled = true;
      const original = btn.getAttribute('data-original-text') || btn.textContent;
      btn.setAttribute('data-original-text', original);
      btn.textContent = 'Saving…';
    });
    // user is saving, no need to warn on unload anymore
    isDirty = false;
  });

  // Date validation (start ≤ end) - KR 13/08/2025
  function parseISO(d) {
    if (!d) return null;
    const parts = d.split('-');
    if (parts.length !== 3) return null;
    const n = parts.map(Number);
    if (n.some(isNaN)) return null;
    return new Date(n[0], n[1] - 1, n[2], 12, 0, 0, 0);
  }
  function setInvalid(input, msg) {
    input.classList.add('is-invalid');
    input.setCustomValidity(msg || 'Invalid');
    let fb = input.parentElement && input.parentElement.querySelector('.invalid-feedback');
    if (!fb) {
      fb = document.createElement('div');
      fb.className = 'invalid-feedback';
      input.parentElement && input.parentElement.appendChild(fb);
    }
    fb.textContent = msg || 'Invalid';
  }
  function clearInvalid(input) {
    input.classList.remove('is-invalid');
    input.setCustomValidity('');
    const fb = input.parentElement && input.parentElement.querySelector('.invalid-feedback');
    if (fb) fb.textContent = '';
  }
  function validateDates() {
    if (!startInput || !endInput) return true;
    const s = parseISO(startInput.value);
    const e = parseISO(endInput.value);
    clearInvalid(startInput);
    clearInvalid(endInput);

    if (s && e && s.getTime() > e.getTime()) {
      setInvalid(endInput, 'End date must be on or after the start date.');
      endInput.focus();
      return false;
    }
    return true;
  }
  if (startInput) on(startInput, 'change', validateDates);
  if (endInput) on(endInput, 'change', validateDates);

 // Description character counter - KR 13/08/2025
  if (descInput) {
    let max = Number(descInput.getAttribute('maxlength')) || 1000;
    let counter = document.createElement('div');
    counter.className = 'form-text text-muted mt-1';
    counter.id = 'desc-counter';
    descInput.insertAdjacentElement('afterend', counter);

    const updateCount = function () {
      const used = descInput.value.length;
      const remain = Math.max(0, max - used);
      counter.textContent = remain + ' characters remaining';
    };
    on(descInput, 'input', updateCount);
    updateCount();
  }

  // Status live badge preview - KR 13/08/2025
  (function statusPreview() {
    if (!statusSelect) return;
    // find a place for the badge: put next to the select
    let holder = document.createElement('div');
    holder.className = 'mt-2';
    statusSelect.insertAdjacentElement('afterend', holder);

    let badge = document.createElement('span');
    badge.className = 'badge';
    holder.appendChild(badge);

    function render() {
      const val = statusSelect.value || '';
      badge.className = 'badge';
      if (val === 'completed') {
        badge.classList.add('bg-success');
        badge.textContent = 'Completed';
      } else if (val === 'ongoing') {
        badge.classList.add('bg-warning', 'text-dark');
        badge.textContent = 'Ongoing';
      } else if (val) {
        badge.classList.add('bg-danger');
        badge.textContent = 'Paused';
      } else {
        badge.classList.add('text-bg-light', 'border');
        badge.textContent = 'Select a status';
      }
    }
    on(statusSelect, 'change', render);
    render();
  })();

// Invite emails chips preview + basic validation + block re-invites - KR 13/08/2025
(function invitePreview() {
  if (!inviteInput) return;

  const already = (window.currentCollaborators || []).map(e => e.toLowerCase());

  let wrap = document.createElement('div');
  wrap.className = 'form-text mt-2';
  inviteInput.insertAdjacentElement('afterend', wrap);

  let chips = document.createElement('div');
  chips.className = 'd-flex flex-wrap gap-2';
  wrap.appendChild(chips);

  let note = document.createElement('div');
  note.className = 'text-muted small mt-1';
  note.textContent = 'Separate multiple emails with commas.';
  wrap.appendChild(note);

  const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  function render() {
    chips.innerHTML = '';
    const parts = (inviteInput.value || '')
      .split(',')
      .map(s => s.trim())
      .filter(Boolean);

    const filtered = [];

    parts.forEach(p => {
      const lower = p.toLowerCase();
      const span = document.createElement('span');

      if (already.includes(lower)) {
        span.className = 'badge bg-danger';
        span.textContent = p + ' (Already invited)';
      } else if (!emailRe.test(p)) {
        span.className = 'badge text-bg-light border';
        span.textContent = p;
      } else {
        span.className = 'badge bg-secondary';
        span.textContent = p;
        filtered.push(p); // keep only valid new emails
      }
      chips.appendChild(span);
    });

    inviteInput.value = filtered.join(', ');
  }

  on(inviteInput, 'input', debounce(render, 100));
  render();
})();
});