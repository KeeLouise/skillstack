document.addEventListener('DOMContentLoaded', function () {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function (alert) {
      setTimeout(function () {
        if (alert.classList.contains('show')) {
          bootstrap.Alert.getOrCreateInstance(alert).close();
        }
      }, 3000); // 3 seconds
    });
  });