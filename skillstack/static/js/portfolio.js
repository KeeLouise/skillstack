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
        }
      }, 150);
    });
  }
})();

//Portfolio share

(function () {
  const shareBtn = document.getElementById('shareBtn');
  if (!shareBtn) return;

  shareBtn.addEventListener('click', async () => {
    const shareData = {
      title: document.title,
      text: "Check out this portfolio!",
      url: window.location.href
    };

    if (navigator.share) {
      try {
        await navigator.share(shareData);
      } catch (err) {
        console.error('Share failed:', err.message);
      }
    } else {
      try {
        await navigator.clipboard.writeText(shareData.url);
        alert("Link copied to clipboard!");
      } catch (err) {
        console.error('Clipboard copy failed:', err.message);
      }
    }
  });
})();