(function () {
  var form = document.getElementById('contact');
  if (!form) return;
  var msg = document.getElementById('msg');
  var btn = form.querySelector('button[type=submit]');
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    msg.className = '';
    btn.disabled = true;
    fetch(form.action, { method: 'POST', body: new FormData(form), headers: { 'Accept': 'application/json' } })
      .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (res) {
        if (res.ok && res.j.ok) {
          form.reset();
          msg.className = 'ok';
          msg.textContent = 'Merci ! Votre demande a bien été envoyée. Nous vous répondrons bientôt.';
        } else {
          msg.className = 'err';
          msg.textContent = (res.j.errors || ['L’envoi a échoué. Réessayez.']).join(' ');
        }
      })
      .catch(function () {
        msg.className = 'err';
        msg.textContent = 'L’envoi a échoué. Vérifiez votre connexion et réessayez.';
      })
      .finally(function () { btn.disabled = false; });
  });
})();
