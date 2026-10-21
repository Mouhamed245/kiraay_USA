(function () {
  var btn = document.getElementById('menuBtn'), nav = document.getElementById('mainNav');
  if (btn && nav) {
    btn.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    nav.addEventListener('click', function (e) {
      if (e.target.tagName === 'A') { nav.classList.remove('open'); btn.setAttribute('aria-expanded', 'false'); }
    });
  }
  var copy = document.getElementById('copyLink');
  if (copy) {
    copy.addEventListener('click', function () {
      var url = copy.getAttribute('data-url');
      if (navigator.clipboard) {
        navigator.clipboard.writeText(url).then(function () { copy.textContent = 'Lien copié'; });
      } else { window.prompt('Copiez ce lien :', url); }
    });
  }
})();
