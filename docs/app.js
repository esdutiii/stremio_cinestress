// Estado global de la aplicación
const state = {
  currentTab: 'novedades',
  searchQuery: '',
  cache: {},
  currentList: []
};

// Elementos del DOM
const elements = {
  grid: document.getElementById('media-grid'),
  searchInput: document.getElementById('search-input'),
  tabButtons: document.querySelectorAll('.tab-btn'),
  modal: document.getElementById('item-modal'),
  modalClose: document.getElementById('modal-close'),
  statMovies: document.getElementById('stat-movies'),
  statSeries: document.getElementById('stat-series'),
  statAnime: document.getElementById('stat-anime'),
  statLinks: document.getElementById('stat-links'),
  statUpdated: document.getElementById('stat-updated'),
};

// Imagen por defecto si un poster falla o no existe
const FALLBACK_POSTER = 'data:image/svg+xml;charset=UTF-8,%3Csvg%20width%3D%22300%22%20height%3D%22450%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3Crect%20width%3D%22300%22%20height%3D%22450%22%20fill%3D%22%23141a29%22%2F%3E%3Ctext%20x%3D%2250%25%22%20y%3D%2250%25%22%20fill%3D%22%2394a3b8%22%20font-size%3D%2220%22%20text-anchor%3D%22middle%22%20dy%3D%22.3em%22%3ESin%20Car%C3%A1tula%3C%2Ftext%3E%3C%2Fsvg%3E';

// Carga las estadísticas iniciales desde stats.json
async function loadStats() {
  try {
    const res = await fetch('data/stats.json');
    if (!res.ok) return;
    const data = await res.json();
    if (elements.statMovies) elements.statMovies.textContent = Number(data.total_movies || 0).toLocaleString();
    if (elements.statSeries) elements.statSeries.textContent = Number(data.total_series || 0).toLocaleString();
    if (elements.statAnime) elements.statAnime.textContent = Number(data.total_anime || 0).toLocaleString();
    if (elements.statLinks) elements.statLinks.textContent = Number(data.total_links || 0).toLocaleString();
    if (elements.statUpdated && data.last_update) {
      elements.statUpdated.textContent = data.last_update.split(' ')[0];
    }
  } catch (err) {
    console.warn('No se pudieron cargar las estadísticas:', err);
  }
}

// Carga los datos de la pestaña seleccionada
async function loadTabData(tabName) {
  state.currentTab = tabName;

  // Actualizamos visualmente las pestañas
  elements.tabButtons.forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tabName);
  });

  // Si ya lo tenemos en caché, lo mostramos inmediatamente
  if (state.cache[tabName]) {
    state.currentList = state.cache[tabName];
    renderGrid();
    return;
  }

  // Mostramos indicador de carga
  elements.grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 60px; color: #94a3b8;">Cargando contenido...</div>';

  try {
    const res = await fetch(`data/${tabName}.json`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    const items = await res.json();
    state.cache[tabName] = items;
    state.currentList = items;
    renderGrid();
  } catch (err) {
    elements.grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 60px; color: #ef4444;">Error al cargar datos de ${tabName}.</div>`;
  }
}

// Filtra y renderiza la cuadrícula de tarjetas
function renderGrid() {
  const query = state.searchQuery.toLowerCase().trim();
  const filtered = state.currentList.filter(item => {
    if (!query) return true;
    const matchTitle = item.title.toLowerCase().includes(query);
    const matchGenre = item.genres.some(g => g.toLowerCase().includes(query));
    const matchYear = item.year.includes(query);
    return matchTitle || matchGenre || matchYear;
  });

  if (filtered.length === 0) {
    elements.grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 60px; color: #94a3b8;">No se encontraron resultados para tu búsqueda.</div>';
    return;
  }

  elements.grid.innerHTML = filtered.map(item => {
    const posterUrl = item.poster || FALLBACK_POSTER;
    const ratingDisplay = item.rating && item.rating !== '0' ? `★ ${item.rating}` : '';
    const typeLabel = item.type === 'series' ? 'Serie' : 'Película';

    return `
      <article class="media-card" onclick="openDetailsModal(${item.tmdb})">
        <div class="poster-wrapper">
          <img class="poster-img" src="${posterUrl}" alt="${item.title}" loading="lazy" onerror="this.src='${FALLBACK_POSTER}'">
          ${ratingDisplay ? `<span class="rating-badge">${ratingDisplay}</span>` : ''}
          <span class="type-badge">${typeLabel}</span>
        </div>
        <div class="card-info">
          <h2 class="card-title" title="${item.title}">${item.title}</h2>
          <div class="card-meta">
            <span>${item.year || 'N/D'}</span>
            <span>${item.category || ''}</span>
          </div>
        </div>
      </article>
    `;
  }).join('');
}

// Abre el modal de detalle del elemento seleccionado
function openDetailsModal(tmdbId) {
  const item = state.currentList.find(i => i.tmdb === tmdbId);
  if (!item) return;

  const backdropEl = document.getElementById('modal-backdrop-img');
  const posterEl = document.getElementById('modal-poster');
  const titleEl = document.getElementById('modal-title');
  const chipsEl = document.getElementById('modal-chips');
  const plotEl = document.getElementById('modal-plot');
  const btnStremio = document.getElementById('btn-open-stremio');
  const btnTmdb = document.getElementById('btn-open-tmdb');

  if (backdropEl) backdropEl.src = item.backdrop || item.poster || '';
  if (posterEl) {
    posterEl.src = item.poster || FALLBACK_POSTER;
    posterEl.onerror = () => { posterEl.src = FALLBACK_POSTER; };
  }
  if (titleEl) titleEl.textContent = item.title;
  if (plotEl) plotEl.textContent = item.plot;

  // Generamos etiquetas de metadatos
  const chips = [];
  if (item.year) chips.push(`<span class="chip">📅 ${item.year}</span>`);
  if (item.rating && item.rating !== '0') chips.push(`<span class="chip" style="color:#fbbf24;">★ ${item.rating}</span>`);
  if (item.category) chips.push(`<span class="chip">🏷️ ${item.category}</span>`);
  item.genres.forEach(g => chips.push(`<span class="chip">${g}</span>`));
  if (chipsEl) chipsEl.innerHTML = chips.join('');

  // Enlaces de acción directa
  const mediaType = item.type === 'series' ? 'series' : 'movie';
  if (btnStremio) {
    // Protocolo nativo de Stremio
    btnStremio.href = `stremio:///detail/${mediaType}/${item.tmdb}`;
  }
  if (btnTmdb) {
    btnTmdb.href = `https://www.themoviedb.org/${mediaType}/${item.tmdb}`;
  }

  elements.modal.classList.add('active');
  document.body.style.overflow = 'hidden';
}

// Cierra el modal de detalle
function closeModal() {
  elements.modal.classList.remove('active');
  document.body.style.overflow = '';
}

// Event Listeners
elements.tabButtons.forEach(btn => {
  btn.addEventListener('click', () => {
    const tab = btn.dataset.tab;
    if (tab && tab !== state.currentTab) {
      loadTabData(tab);
    }
  });
});

elements.searchInput.addEventListener('input', (e) => {
  state.searchQuery = e.target.value;
  renderGrid();
});

elements.modalClose.addEventListener('click', closeModal);
elements.modal.addEventListener('click', (e) => {
  if (e.target === elements.modal) closeModal();
});

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && elements.modal.classList.contains('active')) {
    closeModal();
  }
});

// Inicialización de la aplicación
document.addEventListener('DOMContentLoaded', () => {
  loadStats();
  loadTabData('novedades');
});
