// Live validation for user forms - KR 15/08/2025
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

    // Helpers - KR 15/08/2025
    const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    function scorePassword(pw) {
      let s = 0;
      if (!pw) return 0;
      if (pw.length >= 8) s++;
      if (/[a-z]/.test(pw) && /[A-Z]/.test(pw)) s++;
      if (/\d/.test(pw)) s++;
      if (/[^A-Za-z0-9]/.test(pw)) s++;
      return s; // 0..4
    }
    function labelForScore(s) {
      return ['Very weak','Weak','Okay','Good','Strong'][Math.min(4, Math.max(0, s))];
    }

    function wireFormValidation(form) {
      if (!form || form.__wired) return;
      form.__wired = true;
      form.setAttribute('novalidate', 'novalidate');

      const nameInput  = form.querySelector('input[name="full_name"]') || form.querySelector('input[name$="first_name"]');
      const emailInput = form.querySelector('input[name$="email"]');
      const bioInput   = form.querySelector('textarea[name$="bio"]');
      const pw1        = form.querySelector('input[name="password1"]');
      const pw2        = form.querySelector('input[name="password2"]');

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

      // Email: format only (server handles required/uniqueness) - KR 15/08/2025
      function validateEmail() {
        if (!emailInput) return true;
        const v = (emailInput.value || '').trim();
        if (!v) { // don’t show red just for empty; let server require it
          emailInput.classList.remove('is-invalid', 'is-valid');
          ensureErrorEl(emailInput).textContent = '';
          return true;
        }
        if (!emailRe.test(v)) {
          setFieldError(emailInput, 'Enter a valid email address.');
          return false;
        }
        setFieldError(emailInput, '');
        return true;
      }

      // Passwords: strength (pw1) + match (pw1/pw2) - KR 15/08/2025
      function validatePw1() {
        if (!pw1) return true;
        const v = pw1.value || '';
        if (v.length < 8) {
          setFieldError(pw1, 'Password must be at least 8 characters.');
          setMeter(labelForScore(scorePassword(v)));
          return false;
        }
        setFieldError(pw1, '');
        setMeter(labelForScore(scorePassword(v)));
        return true;
      }
      function validatePw2() {
        if (!pw1 || !pw2) return true;
        const a = pw1.value || '';
        const b = pw2.value || '';
        if (b && a !== b) {
          setFieldError(pw2, 'Passwords do not match.');
          return false;
        }
        // Only mark valid if user typed something and it matches
        if (b && a === b) setFieldError(pw2, '');
        else {
          pw2.classList.remove('is-invalid','is-valid');
          ensureErrorEl(pw2).textContent = '';
        }
        return a === b;
      }
      // strength meter under pw1 - KR 15/08/2025
      function setMeter(text) {
        if (!pw1) return;
        let meter = pw1.nextElementSibling && pw1.nextElementSibling.classList && pw1.nextElementSibling.classList.contains('form-text')
          ? pw1.nextElementSibling
          : null;
        if (!meter) {
          meter = document.createElement('div');
          meter.className = 'form-text small text-muted';
          pw1.insertAdjacentElement('afterend', meter);
        }
        meter.textContent = text;
      }

      // Bio: live remaining counter + max length check - KR 15/08/2025
      function validateBio() {
        if (!bioInput) return true;
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
      if (nameInput)  { nameInput.addEventListener('input', validateName);  nameInput.addEventListener('blur', validateName); }
      if (emailInput) { emailInput.addEventListener('input', validateEmail); emailInput.addEventListener('blur', validateEmail); }
      if (pw1)        { pw1.addEventListener('input', validatePw1);         pw1.addEventListener('blur', validatePw1); }
      if (pw2)        { pw2.addEventListener('input', validatePw2);         pw2.addEventListener('blur', validatePw2); }
      if (bioInput)   { bioInput.addEventListener('input', validateBio);    bioInput.addEventListener('blur', validateBio); }

      // Initial render (show bio counter immediately) - KR 15/08/2025
      validateBio();

      // Submit gate - KR 15/08/2025
      form.addEventListener('submit', (e) => {
        const ok =
          (validateName()  !== false) &&
          (validateEmail() !== false) &&
          (validatePw1()   !== false) &&
          (validatePw2()   !== false) &&
          (validateBio()   !== false);

        if (!ok) {
          e.preventDefault();
          e.stopPropagation();
          const firstBad = form.querySelector('.is-invalid');
          if (firstBad) firstBad.focus();
        }
      });
    }

    ['registerForm', 'editProfileForm', 'userUpdateForm', 'profileForm']
      .forEach(id => wireFormValidation(q('#' + id)));

    qa('form').forEach((form) => {
      if (form.__wired) return;
      const looksUserForm =
        form.querySelector('input[name="full_name"]') ||
        form.querySelector('input[name$="first_name"]') ||
        form.querySelector('input[name$="email"]') ||
        form.querySelector('input[name="password1"]') ||
        form.querySelector('input[name="password2"]') ||
        form.querySelector('textarea[name$="bio"]');
      if (looksUserForm) wireFormValidation(form);
    });
  })();
});