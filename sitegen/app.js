(function () {
  var input = document.getElementById('nav-filter');
  var list = document.getElementById('nav-list');
  if (input && list) {
    input.addEventListener('input', function () {
      var q = input.value.trim().toLowerCase();
      list.querySelectorAll('.nav-group').forEach(function (group) {
        var visible = 0;
        group.querySelectorAll('li').forEach(function (li) {
          var hit = !q || li.textContent.toLowerCase().indexOf(q) !== -1;
          li.style.display = hit ? '' : 'none';
          if (hit) visible++;
        });
        group.style.display = visible ? '' : 'none';
      });
    });
  }

  var here = decodeURIComponent(location.pathname.split('/').pop() || 'index.html');
  document.querySelectorAll('.sidebar a').forEach(function (a) {
    var href = a.getAttribute('href') || '';
    var name = decodeURIComponent(href.split('/').pop());
    if (name === here) {
      a.classList.add('active');
      a.scrollIntoView({ block: 'nearest' });
    }
  });
})();
