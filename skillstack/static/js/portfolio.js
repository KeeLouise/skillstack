(function(){
  const urlInput = document.querySelector('#id_url');
  const titleInput = document.querySelector('#id_title');
  const liveTitle = document.getElementById('liveTitle');
  const liveUrl   = document.getElementById('liveUrl');
  const liveThumb = document.getElementById('liveThumb');

  function setThumb(src){
    if (!src) {
      liveThumb.innerHTML = '<div class="preview-placeholder">Preview</div>';
      liveThumb.style.backgroundImage = '';
      return;
    }
    liveThumb.innerHTML = '';
    liveThumb.style.backgroundImage = `url("${src}")`;
  }

  function updateTexts(){
    if (titleInput) liveTitle.textContent = titleInput.value || 'Title will appear here';
    if (urlInput)   liveUrl.textContent   = urlInput.value || 'https://your-link.example';
  }
  updateTexts();

  if (titleInput) titleInput.addEventListener('input', updateTexts);
  if (urlInput) {
    urlInput.addEventListener('input', updateTexts);
    let t;
    urlInput.addEventListener('blur', function(){
      const v = urlInput.value.trim();
      if (!/^https?:\/\//i.test(v)) return;
      clearTimeout(t);
      t = setTimeout(async function(){
        try{
          const res = await fetch("{% url 'portfolio_preview_api' %}?url=" + encodeURIComponent(v));
          if (!res.ok) return;
          const data = await res.json();
          if (!titleInput.value && data.title) {
            titleInput.value = data.title;
            updateTexts();
          }
          setThumb(data.image_url || '');
        }catch(e){}
      }, 150);
    });
  }
})();