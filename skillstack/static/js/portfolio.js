// Portfolio form live preview + OG fetch - KR 15/08/2025
(function () {
  const form = document.getElementById('portfolioForm');
  if (!form) return;
  const previewApi = form.dataset.previewUrl || '/portfolio/preview/';

  const urlInput   = document.querySelector('#id_url');
  const titleInput = document.querySelector('#id_title');
  const liveTitle  = document.getElementById('liveTitle');
  const liveUrl    = document.getElementById('liveUrl');
  const liveThumb  = document.getElementById('liveThumb');

  function setThumb(src) {
    if (!liveThumb) return;
    if (!src) {
      liveThumb.innerHTML = '<div class="preview-placeholder">Preview</div>';
      liveThumb.style.backgroundImage = '';
      return;
    }
    liveThumb.innerHTML = '';
    liveThumb.style.backgroundImage = `url("${src}")`;
  }

  function updateTexts() {
    if (liveTitle && titleInput) {
      liveTitle.textContent = titleInput.value || 'Title will appear here';
    }
    if (liveUrl && urlInput) {
      liveUrl.textContent = urlInput.value || 'https://your-link.example';
    }
  }

  updateTexts();

  if (titleInput) titleInput.addEventListener('input', updateTexts);
  if (urlInput) {
    urlInput.addEventListener('input', updateTexts);

    let debounceTimer;
    urlInput.addEventListener('blur', function () {
      const v = (urlInput.value || '').trim();
      if (!/^https?:\/\//i.test(v)) return;

      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(async function () {
        try {
          const res = await fetch(previewApi + '?url=' + encodeURIComponent(v), {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
          });
          if (!res.ok) return;

          const data = await res.json();

          if (titleInput && !titleInput.value && data.title) {
            titleInput.value = data.title;
            updateTexts();
          }

          setThumb(data.image_url || '');
        } catch (e) {
          // ignore network errors in preview - KR 15/08/2025
        }
      }, 150);
    });
  }
})();



// Portfolio share - KR 15/08/2025

(function () {
  // Utility: safe clipboard copy with multiple fallbacks - KR 15/08/2025
  async function copyToClipboard(text) {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
        return true;
      }
    } catch (_) {  }

    try {
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.setAttribute('readonly', '');
      ta.style.position = 'fixed';
      ta.style.top = '-1000px';
      document.body.appendChild(ta);
      ta.select();
      ta.setSelectionRange(0, ta.value.length);
      const ok = document.execCommand('copy');
      document.body.removeChild(ta);
      return ok;
    } catch (_) {
      return false;
    }
  }

  // Handler that reads data attributes and shares/copies - KR 15/08/2025
  async function handleShareClick(btn) {
    const shareUrl   = btn.dataset.shareUrl   || window.location.href;
    const shareTitle = btn.dataset.shareTitle || 'Check out my portfolio!';
    const shareText  = btn.dataset.shareText  || "Here's my work:";

    if (!shareUrl) return;

    if (btn.dataset.busy === '1') return;
    btn.dataset.busy = '1';

    try {
      // Web Share API path - KR 15/08/2025
      if (navigator.share) {
        try {
          await navigator.share({ title: shareTitle, text: shareText, url: shareUrl });
          return;
        } catch (err) {
        }
      }

      // Clipboard fallback path - KR 15/08/2025
      const ok = await copyToClipboard(shareUrl);
      if (ok) {
        alert('Link copied to clipboard!');
      } else {
        // Final fallback: prompt so user can copy manually - KR 15/08/2025
        window.prompt('Copy this link:', shareUrl);
      }
    } finally {
      // release busy flag - KR 15/08/2025
      delete btn.dataset.busy;
    }
  }

  // Bind single page-level button if present - KR 15/08/2025
  const single = document.getElementById('shareBtn');
  if (single) {
    single.addEventListener('click', () => handleShareClick(single));
  }

  // Bind any per-card buttons using a common selector - KR 15/08/2025
  const allBtns = document.querySelectorAll('[data-share-url]');
  allBtns.forEach((btn) => {
    // avoid double-binding the page-level one if both patterns used - KR 15/08/2025
    if (btn === single) return;
    btn.addEventListener('click', () => handleShareClick(btn));
  });
})();