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