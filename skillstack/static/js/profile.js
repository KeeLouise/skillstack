(function () {
  const input = document.querySelector('input[type="file"][name$="profile_picture"]');
  if (!input) return;
  const previewImg = document.getElementById('avatarPreview');
  const fallback = document.getElementById('avatarFallback');

  input.addEventListener('change', function (e) {
    const file = e.target.files && e.target.files[0];
    if (!file) return;
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
        const avatar = document.querySelector('.avatar');
        if (avatar) {
          if (fallback) fallback.remove();
          avatar.appendChild(img);
        }
      }
    };
    reader.readAsDataURL(file);
  });
})();