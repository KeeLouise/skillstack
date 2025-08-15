document.addEventListener('DOMContentLoaded', function () {
    (function () {
  const q  = (s, r=document) => r.querySelector(s);
  const qa = (s, r=document) => Array.from(r.querySelectorAll(s));

  // Ensure an error <div> sits right after the input - KR 15/08/2025
  function ensureErrorEl(input) {
    let el = input.nextElementSibling;
    if (!el || !el.classList || !el.classList.contains('invalid-feedback')) {
      el = document.createElement('div');
      el.className = 'invalid-feedback';
      input.insertAdjacentElement('afterend', el);
    }
    return el;
  }

  function setFieldError(input, msg) {
    const err = ensureErrorEl(input);
    if (msg) {
      input.classList.add('is-invalid');
      input.classList.remove('is-valid');
      err.textContent = msg;
    } else {
      input.classList.remove('is-invalid');
      input.classList.add('is-valid');
      err.textContent = '';
    }
  }

  // Basic email regex - KR 15/08/2025
  const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  function wireFormValidation(form) {
    if (!form) return;
    form.setAttribute('novalidate', 'novalidate');

    const nameInput  = form.querySelector('input[name$="first_name"]');
    const emailInput = form.querySelector('input[name$="email"]');
    const bioInput   = form.querySelector('textarea[name$="bio"]');

    // Name: at least 2 visible characters - KR 15/08/2025
    function validateName() {
      if (!nameInput) return true;
      const v = (nameInput.value || '').trim();
      if (v.length < 2) {
        setFieldError(nameInput, 'Name must be at least 2 characters.');
        return false;
      }
      setFieldError(nameInput, '');
      return true;
    }

    // Email: format only (server still checks uniqueness) - KR 15/08/2025
    function validateEmail() {
      if (!emailInput) return true;
      const v = (emailInput.value || '').trim();
      if (!emailRe.test(v)) {
        setFieldError(emailInput, 'Enter a valid email address.');
        return false;
      }
      setFieldError(emailInput, '');
      return true;
    }

    // Bio: live remaining counter + max length check - KR 15/08/2025
    function validateBio() {
      if (!bioInput) return true;

      // Reuse existing counter from profile.js if present, otherwise create - KR 15/08/2025
      let counter = document.getElementById('bio-counter');
      if (!counter) {
        counter = document.createElement('div');
        counter.id = 'bio-counter';
        counter.className = 'text-muted small mt-1';
        bioInput.parentNode.appendChild(counter);
      }

      const maxAttr = bioInput.getAttribute('maxlength');
      const max = (maxAttr && Number(maxAttr)) || 300;
      const used = bioInput.value.length;
      const remaining = Math.max(0, max - used);

      counter.textContent = `${remaining} characters remaining`;

      if (used > max) {
        setFieldError(bioInput, `Bio cannot exceed ${max} characters.`);
        return false;
      }
      setFieldError(bioInput, '');
      return true;
    }

    // Live inline checks - KR 15/08/2025
    if (nameInput)  nameInput.addEventListener('input', validateName);
    if (emailInput) emailInput.addEventListener('input', validateEmail);
    if (bioInput)   bioInput.addEventListener('input',  validateBio);
    if (nameInput)  nameInput.addEventListener('blur', validateName);
    if (emailInput) emailInput.addEventListener('blur', validateEmail);
    if (bioInput)   bioInput.addEventListener('blur',  validateBio);

    // Initial render (shows bio counter immediately) - KR 15/08/2025
    validateBio();

    form.addEventListener('submit', (e) => {
      const ok =
        (validateName()  !== false) &
        (validateEmail() !== false) &
        (validateBio()   !== false);

      if (!ok) {
        e.preventDefault();
        e.stopPropagation();
        const firstBad = form.querySelector('.is-invalid');
        if (firstBad) firstBad.focus();
      }
    });
  }

  ['editProfileForm', 'registerForm', 'userUpdateForm', 'profileForm']
    .forEach(id => wireFormValidation(q('#' + id)));

  qa('form').forEach((form) => {
    if (form.__wired) return;
    const looksUsery =
      form.querySelector('input[name$="first_name"]') ||
      form.querySelector('input[name$="email"]') ||
      form.querySelector('textarea[name$="bio"]');
    if (looksyUsery) { // typo fix
      form.__wired = true;
      wireFormValidation(form);
    }
  });
 })();
});