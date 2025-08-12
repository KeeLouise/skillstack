(function () {
  // Helpers - KR 12/08/2025
  function $(sel, ctx) { return (ctx || document).querySelector(sel); }
  function $all(sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); }
  function on(el, ev, fn, opts) { if (el) el.addEventListener(ev, fn, opts || false); }

  // Avatar Preview - KR 12/08/2025
  (function avatarPreview() {
    const input = document.querySelector('input[type="file"][name$="profile_picture"]');
    if (!input) return;
    const previewImg = document.getElementById('avatarPreview');
    const fallback = document.getElementById('avatarFallback');

    on(input, 'change', function (e) {
      const file = e.target.files && e.target.files[0];
      if (!file) return;

      if (!file.type || !/^image\//i.test(file.type)) return;

      const reader = new FileReader();
      reader.onload = function (ev) {
        if (previewImg) {
          previewImg.src = ev.target.result;
          previewImg.style.display = '';
        } else {
          const img = document.createElement('img');
          img.id = 'avatarPreview';
          img.className = 'avatar-img';
          img.alt = 'Profile picture';
          img.src = ev.target.result;
          const avatar = $('.avatar');
          if (avatar) {
            if (fallback) fallback.remove();
            avatar.appendChild(img);
          }
        }
        // Recalculate completion if progress bar is present - KR 12/08/2025
        updateProfileCompletion();
      };
      reader.readAsDataURL(file);
    });
  })();

  // Bio Character Counter - KR 12/08/2025
  (function bioCounter() {
    const bio = document.querySelector('textarea[name$="bio"]');
    const counter = document.getElementById('bio-counter');
    if (!bio || !counter) return;

    const max = Number(bio.getAttribute('maxlength')) || Number(counter.getAttribute('data-max')) || 300;

    function render() {
      const used = bio.value.length;
      const remaining = Math.max(0, max - used);
      counter.textContent = remaining + ' characters remaining';
    }

    on(bio, 'input', render);
    render();
  })();

  // Collapsible Recent Projects - KR 12/08/2025
  (function recentProjectsToggle() {
    const wrap = document.getElementById('recent-projects');
    const btn = document.getElementById('toggle-projects');
    if (!wrap || !btn) return;

    function isHidden() {
      return wrap.classList.contains('d-none') || wrap.style.display === 'none';
    }

    function show() {
      wrap.classList.remove('d-none');
      wrap.style.display = '';
      btn.setAttribute('aria-expanded', 'true');
      btn.textContent = btn.getAttribute('data-label-hide') || 'Hide Projects';
    }

    function hide() {
      wrap.classList.add('d-none');
      btn.setAttribute('aria-expanded', 'false');
      btn.textContent = btn.getAttribute('data-label-show') || 'Show Projects';
    }

    on(btn, 'click', function (e) {
      e.preventDefault();
      if (isHidden()) show(); else hide();
    });

    if (btn.getAttribute('data-start-collapsed') === 'true') {
      hide();
    }
  })();

  // Profile completion progress - KR 12/08/2025
  (function profileCompletion() {
    const bar = document.getElementById('profile-progress');
    if (!bar) return;

    function hasValue(v) {
      return v !== undefined && v !== null && String(v).trim() !== '';
    }

    function compute() {
      // Pull from the DOM - KR 12/08/2025
      const avatarImg = document.getElementById('avatarPreview');
      const avatarSet = !!(avatarImg && avatarImg.getAttribute('src'));

      const nameEl = document.querySelector('[data-field="name"]');
      const emailEl = document.querySelector('[data-field="email"]');
      const companyEl = document.querySelector('[data-field="company"]');
      const bioEl = document.querySelector('[data-field="bio"]');

      // Fallback to form fields if data-field spans aren’t present - KR 12/08/2025
      const nameVal =
        (nameEl && nameEl.textContent) ||
        (document.querySelector('input[name$="first_name"]') || {}).value;
      const emailVal =
        (emailEl && emailEl.textContent) ||
        (document.querySelector('input[name$="email"]') || {}).value;
      const companyVal =
        (companyEl && companyEl.textContent) ||
        (document.querySelector('input[name$="company"]') || {}).value;
      const bioVal =
        (bioEl && bioEl.textContent) ||
        (document.querySelector('textarea[name$="bio"]') || {}).value;

      const checks = [
        avatarSet,
        hasValue(nameVal),
        hasValue(emailVal),
        hasValue(companyVal),
        hasValue(bioVal)
      ];

      const complete = checks.filter(Boolean).length;
      const total = checks.length;
      const pct = Math.round((complete / total) * 100);

      return { pct, complete, total };
    }

    function render() {
      const { pct } = compute();
      const inner = bar.querySelector('.progress-bar');
      if (inner) {
        inner.style.width = pct + '%';
        inner.setAttribute('aria-valuenow', pct);
        inner.textContent = pct + '%';
      } else {
        bar.style.width = pct + '%';
        bar.textContent = pct + '%';
      }
    }

    // Re-render on inputs that affect completion - KR 12/08/2025
    ['input', 'change'].forEach(evt => {
      $all('input[name$="first_name"], input[name$="email"], input[name$="company"], textarea[name$="bio"]').forEach(el => {
        on(el, evt, render);
      });
    });

    // Initial render - KR 12/08/2025
    render();

    // Expose for avatar preview callback - KR 12/08/2025
    window.updateProfileCompletion = render;
  })();

})();