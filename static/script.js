/* script.js — El Correo News Digest */

var SECCIONES = [];   // datos cargados desde /api/noticias

/* ── Carga de noticias ──────────────────────────────────── */
function cargarNoticias() {
  var btn = document.getElementById('btn-actualizar');
  var estado = document.getElementById('estado');
  var cont = document.getElementById('secciones');

  btn.disabled = true;
  btn.textContent = '⏳ Cargando…';
  estado.className = 'estado-carga';
  cont.innerHTML = '';

  fetch('/api/noticias')
    .then(function(r) { return r.json(); })
    .then(function(data) {
      if (!data.ok) throw new Error(data.error || 'Error desconocido');
      SECCIONES = data.secciones;
      renderSecciones();
      actualizarPie();
    })
    .catch(function(err) {
      estado.innerHTML =
        '<p style="color:#c00;font-family:sans-serif">⚠️ Error al cargar: ' +
        err.message + '</p>' +
        '<button onclick="cargarNoticias()" style="margin-top:12px;padding:8px 20px;' +
        'background:#c8001e;color:#fff;border:none;border-radius:20px;cursor:pointer;' +
        'font-size:.85rem">Reintentar</button>';
    })
    .finally(function() {
      btn.disabled = false;
      btn.textContent = '↻ Actualizar';
    });
}

/* ── Renderizado ────────────────────────────────────────── */
function renderSecciones() {
  var estado = document.getElementById('estado');
  var cont = document.getElementById('secciones');
  var nav = document.getElementById('jump-nav');

  estado.className = 'estado-carga oculto';
  cont.innerHTML = '';
  nav.innerHTML = '';

  SECCIONES.forEach(function(sec) {
    if (!sec.arts || sec.arts.length === 0) return;

    // Botón de salto
    var jb = document.createElement('button');
    jb.className = 'jump-btn';
    jb.textContent = sec.name;
    jb.style.borderBottom = '3px solid ' + sec.color;
    jb.onclick = function() {
      document.getElementById('sec-' + sec.id).scrollIntoView({ behavior: 'smooth', block: 'start' });
    };
    nav.appendChild(jb);

    // Sección
    var secDiv = document.createElement('div');
    secDiv.className = 'seccion';
    secDiv.id = 'sec-' + sec.id;

    // Cabecera de sección
    var cab = document.createElement('div');
    cab.className = 'sec-cabecera';
    cab.style.background = sec.color;
    cab.innerHTML =
      '<span class="sec-titulo">' + sec.name + '</span>' +
      '<span style="display:flex;align-items:center;gap:10px">' +
        '<span class="sec-contador">' + sec.arts.length + ' noticias</span>' +
        '<span class="sec-toggle">▾</span>' +
      '</span>';
    cab.onclick = function() { toggleSec(secDiv); };
    secDiv.appendChild(cab);

    // Grid de artículos
    var body = document.createElement('div');
    body.className = 'sec-body';
    var grid = document.createElement('div');
    grid.className = 'art-grid';
    body.appendChild(grid);
    secDiv.appendChild(body);

    sec.arts.forEach(function(art) {
      grid.appendChild(crearCard(art, sec.color));
    });

    // Fijar max-height para animación
    requestAnimationFrame(function() {
      body.style.maxHeight = body.scrollHeight + 'px';
    });

    cont.appendChild(secDiv);
  });

  // Mensaje "sin resultados" para búsqueda
  var noRes = document.createElement('div');
  noRes.className = 'no-resultados';
  noRes.id = 'no-resultados';
  noRes.innerHTML = '<p>No se encontraron noticias para tu búsqueda.</p>';
  cont.appendChild(noRes);
}

function crearCard(art, color) {
  var card = document.createElement('div');
  card.className = 'art-card';
  card.dataset.titulo = (art.t || '').toLowerCase();
  card.dataset.resumen = (art.res || '').toLowerCase();

  // Imagen
  var imgWrap = document.createElement('div');
  imgWrap.className = 'art-img-wrap';
  if (art.img) {
    var img = document.createElement('img');
    // Usar el proxy local para evitar problemas de Referer
    img.src = '/proxy/img?url=' + encodeURIComponent(art.img);
    img.alt = art.t || '';
    img.loading = 'lazy';
    img.onerror = function() {
      imgWrap.innerHTML = '<div class="art-no-img">📰</div>';
    };
    imgWrap.appendChild(img);
  } else {
    imgWrap.innerHTML = '<div class="art-no-img">📰</div>';
  }
  card.appendChild(imgWrap);

  // Cuerpo
  var body = document.createElement('div');
  body.className = 'art-body';

  var titulo = document.createElement('div');
  titulo.className = 'art-title';
  if (art.url) {
    titulo.innerHTML = '<a href="' + art.url + '" target="_blank" rel="noopener">' +
      escHtml(art.t) + '</a>';
  } else {
    titulo.textContent = art.t || '';
  }
  body.appendChild(titulo);

  if (art.res) {
    var resumen = document.createElement('p');
    resumen.className = 'art-summary';
    resumen.textContent = art.res;
    body.appendChild(resumen);
  }

  if (art.url) {
    var mas = document.createElement('a');
    mas.className = 'art-more';
    mas.href = art.url;
    mas.target = '_blank';
    mas.rel = 'noopener';
    mas.textContent = 'Leer más →';
    mas.style.color = color;
    body.appendChild(mas);
  }

  card.appendChild(body);
  return card;
}

/* ── Colapsar/expandir sección ──────────────────────────── */
function toggleSec(secDiv) {
  var body = secDiv.querySelector('.sec-body');
  var colapsada = secDiv.classList.contains('colapsada');
  if (colapsada) {
    secDiv.classList.remove('colapsada');
    body.style.maxHeight = body.scrollHeight + 'px';
  } else {
    secDiv.classList.add('colapsada');
    body.style.maxHeight = '0';
  }
}

/* ── Búsqueda / filtro ──────────────────────────────────── */
function filtrar(q) {
  var termino = q.toLowerCase().trim();
  var hayResultados = false;

  document.querySelectorAll('.seccion').forEach(function(secDiv) {
    var visibles = 0;
    secDiv.querySelectorAll('.art-card').forEach(function(card) {
      var match = !termino ||
        card.dataset.titulo.includes(termino) ||
        card.dataset.resumen.includes(termino);
      card.classList.toggle('oculta', !match);
      if (match) visibles++;
    });

    if (termino) {
      // Expandir secciones con resultados, ocultar las vacías
      if (visibles > 0) {
        secDiv.style.display = '';
        secDiv.classList.remove('colapsada');
        var body = secDiv.querySelector('.sec-body');
        body.style.maxHeight = body.scrollHeight + 'px';
        hayResultados = true;
      } else {
        secDiv.style.display = 'none';
      }
    } else {
      secDiv.style.display = '';
    }
  });

  var noRes = document.getElementById('no-resultados');
  if (noRes) {
    noRes.style.display = (termino && !hayResultados) ? 'block' : 'none';
  }
}

/* ── Pie de página ──────────────────────────────────────── */
function actualizarPie() {
  var pie = document.getElementById('pie-fecha');
  if (!pie) return;
  var now = new Date();
  var opts = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' };
  pie.textContent = 'Actualizado: ' + now.toLocaleDateString('es-ES', opts);
}

/* ── Utilidades ─────────────────────────────────────────── */
function escHtml(str) {
  return (str || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/* ── Inicio ─────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', cargarNoticias);
