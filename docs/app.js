// Estado global de la aplicación
const state = {
  currentTab: 'novedades',
  searchQuery: '',
  cache: {},
  currentList: [],
  selectedItem: null,
  activeSeason: null,
  linksOpen: false,
  unlockedPassword: sessionStorage.getItem('cinestress_vault_key') || ''
};

// Hash SHA-256 de verificación (la contraseña en texto plano no se expone en el código web)
const AUTH_HASH = "ce66024462bdc05cf6c58ce072a22d5b6772b8bda9aa82a1d93c7fdab57a8a30";

// Elementos del DOM
const elements = {
  grid: document.getElementById('media-grid'),
  searchInput: document.getElementById('search-input'),
  tabButtons: document.querySelectorAll('.tab-btn'),
  modal: document.getElementById('item-modal'),
  modalClose: document.getElementById('modal-close'),
  statMovies: document.getElementById('stat-movies'),
  statSeries: document.getElementById('stat-series'),
  statDocu: document.getElementById('stat-docu'),
  statCartoons: document.getElementById('stat-cartoons'),
  statAnime: document.getElementById('stat-anime'),
  statMusic: document.getElementById('stat-music'),
  statRetro: document.getElementById('stat-retro'),
  statLinks: document.getElementById('stat-links'),
  btnToggleLinks: document.getElementById('btn-toggle-links'),
  btnTmdb: document.getElementById('btn-open-tmdb'),
  linksContainer: document.getElementById('links-container'),
  linksAuthBox: document.getElementById('links-auth-box'),
  linksContent: document.getElementById('links-content'),
  inputPassword: document.getElementById('input-password'),
  btnUnlock: document.getElementById('btn-unlock'),
  authError: document.getElementById('auth-error'),
  linksCount: document.getElementById('links-count'),
  seriesSeasonBar: document.getElementById('series-season-bar'),
  linksItemsList: document.getElementById('links-items-list')
};

// Imagen por defecto si un poster falla o no existe
const FALLBACK_POSTER = 'data:image/svg+xml;charset=UTF-8,%3Csvg%20width%3D%22300%22%20height%3D%22450%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3Crect%20width%3D%22300%22%20height%3D%22450%22%20fill%3D%22%23141a29%22%2F%3E%3Ctext%20x%3D%2250%25%22%20y%3D%2250%25%22%20fill%3D%22%2394a3b8%22%20font-size%3D%2220%22%20text-anchor%3D%22middle%22%20dy%3D%22.3em%22%3ESin%20Car%C3%A1tula%3C%2Ftext%3E%3C%2Fsvg%3E';

// Calcula el hash SHA-256 de una cadena de texto
async function sha256(message) {
  const msgUint8 = new TextEncoder().encode(message);
  const hashBuffer = await crypto.subtle.digest('SHA-256', msgUint8);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

// Descifra la lista de enlaces con la Web Crypto API (AES-GCM 256 bits)
async function decryptLinksPayload(b64Payload, passwordStr) {
  if (!b64Payload || !passwordStr) return [];
  try {
    const rawStr = atob(b64Payload);
    const rawBytes = new Uint8Array(rawStr.length);
    for (let i = 0; i < rawStr.length; i++) {
      rawBytes[i] = rawStr.charCodeAt(i);
    }

    const iv = rawBytes.slice(0, 12);
    const ciphertextWithTag = rawBytes.slice(12);

    const enc = new TextEncoder();
    const keyHash = await crypto.subtle.digest('SHA-256', enc.encode(passwordStr));

    const cryptoKey = await crypto.subtle.importKey(
      'raw',
      keyHash,
      { name: 'AES-GCM' },
      false,
      ['decrypt']
    );

    const decryptedBuffer = await crypto.subtle.decrypt(
      { name: 'AES-GCM', iv: iv },
      cryptoKey,
      ciphertextWithTag
    );

    const decryptedText = new TextDecoder().decode(decryptedBuffer);
    return JSON.parse(decryptedText);
  } catch (err) {
    console.error("Error al descifrar enlaces:", err);
    return [];
  }
}

// Copia una URL al portapapeles con confirmación visual
function copyLinkUrl(url, btnElement) {
  if (!url) return;
  navigator.clipboard.writeText(url).then(() => {
    const originalText = btnElement.innerHTML;
    btnElement.innerHTML = '✓ ¡Copiado!';
    btnElement.classList.add('copied');
    setTimeout(() => {
      btnElement.innerHTML = originalText;
      btnElement.classList.remove('copied');
    }, 2000);
  }).catch(() => {
    const tmp = document.createElement('textarea');
    tmp.value = url;
    document.body.appendChild(tmp);
    tmp.select();
    document.execCommand('copy');
    document.body.removeChild(tmp);
    btnElement.innerHTML = '✓ ¡Copiado!';
    btnElement.classList.add('copied');
    setTimeout(() => {
      btnElement.innerHTML = '📋 Copiar';
      btnElement.classList.remove('copied');
    }, 2000);
  });
}

// Carga las estadísticas iniciales desde stats.json
async function loadStats() {
  try {
    const res = await fetch('data/stats.json');
    if (!res.ok) return;
    const data = await res.json();
    if (elements.statMovies) elements.statMovies.textContent = Number(data.movies || 0).toLocaleString();
    if (elements.statSeries) elements.statSeries.textContent = Number(data.series || 0).toLocaleString();
    if (elements.statDocu) elements.statDocu.textContent = Number(data.documentaries || 0).toLocaleString();
    if (elements.statCartoons) elements.statCartoons.textContent = Number(data.cartoons || 0).toLocaleString();
    if (elements.statAnime) elements.statAnime.textContent = Number(data.anime || 0).toLocaleString();
    if (elements.statMusic) elements.statMusic.textContent = Number(data.music || 0).toLocaleString();
    if (elements.statRetro) elements.statRetro.textContent = Number(data.retro || 0).toLocaleString();
    if (elements.statLinks) elements.statLinks.textContent = Number(data.total_links || 0).toLocaleString();
  } catch (err) {
    console.warn('No se pudieron cargar las estadísticas:', err);
  }
}

// Carga los datos de la pestaña seleccionada
async function loadTabData(tabName) {
  state.currentTab = tabName;

  elements.tabButtons.forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tabName);
  });

  if (state.cache[tabName]) {
    state.currentList = state.cache[tabName];
    renderGrid();
    return;
  }

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
      <article class="media-card" onclick="openDetailsModal(${item.tmdb}, '${item.type}')">
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
function openDetailsModal(tmdbId, itemType) {
  const item = state.currentList.find(i => i.tmdb === tmdbId && (!itemType || i.type === itemType))
            || state.currentList.find(i => i.tmdb === tmdbId);
  if (!item) return;

  state.selectedItem = item;
  state.linksOpen = false;
  state.activeSeason = null;

  const backdropEl = document.getElementById('modal-backdrop-img');
  const posterEl = document.getElementById('modal-poster');
  const titleEl = document.getElementById('modal-title');
  const chipsEl = document.getElementById('modal-chips');
  const plotEl = document.getElementById('modal-plot');

  if (backdropEl) backdropEl.src = item.backdrop || item.poster || '';
  if (posterEl) {
    posterEl.src = item.poster || FALLBACK_POSTER;
    posterEl.onerror = () => { posterEl.src = FALLBACK_POSTER; };
  }
  if (titleEl) titleEl.textContent = item.title;
  if (plotEl) plotEl.textContent = item.plot;

  // Generamos etiquetas de información
  const chips = [];
  if (item.year) chips.push(`<span class="chip">📅 ${item.year}</span>`);
  if (item.rating && item.rating !== '0') chips.push(`<span class="chip" style="color:#fbbf24;">★ ${item.rating}</span>`);
  if (item.category) chips.push(`<span class="chip">🏷️ ${item.category}</span>`);
  item.genres.forEach(g => chips.push(`<span class="chip">${g}</span>`));
  if (chipsEl) chipsEl.innerHTML = chips.join('');

  // Enlace a TMDB: Ocultamos en TV & Retro y usamos /tv/ para series y /movie/ para peliculas
  const isRetro = state.currentTab === 'retro' || 
                  item.category === 'Retro' || 
                  item.category === 'Telenovela' || 
                  item.category === 'Reality';

  if (elements.btnTmdb) {
    if (isRetro) {
      elements.btnTmdb.style.display = 'none';
    } else {
      elements.btnTmdb.style.display = 'inline-flex';
      const tmdbType = item.type === 'series' ? 'tv' : 'movie';
      elements.btnTmdb.href = `https://www.themoviedb.org/${tmdbType}/${item.tmdb}`;
    }
  }

  // Reseteamos el estado del botón y la sección de enlaces
  if (elements.btnToggleLinks) {
    elements.btnToggleLinks.classList.remove('active-open');
    elements.btnToggleLinks.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
        <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
      </svg>
      Ver Enlaces
    `;
  }
  if (elements.linksContainer) elements.linksContainer.style.display = 'none';
  if (elements.authError) elements.authError.style.display = 'none';
  if (elements.inputPassword) elements.inputPassword.value = '';

  elements.modal.classList.add('active');
  document.body.style.overflow = 'hidden';
}

// Cierra el modal de detalle
function closeModal() {
  elements.modal.classList.remove('active');
  document.body.style.overflow = '';
  state.linksOpen = false;
  state.selectedItem = null;
}

// Renderiza los enlaces descifrados en el DOM
async function renderDecryptedLinks() {
  if (!state.selectedItem) return;

  const links = await decryptLinksPayload(state.selectedItem.links_enc, state.unlockedPassword);

  if (!links || links.length === 0) {
    if (elements.linksCount) elements.linksCount.textContent = '0 enlaces';
    if (elements.seriesSeasonBar) elements.seriesSeasonBar.style.display = 'none';
    if (elements.linksItemsList) {
      elements.linksItemsList.innerHTML = '<div class="no-links-msg">ℹ️ No hay enlaces registrados para este título en la base de datos.</div>';
    }
    return;
  }

  // Si es película, mostramos todas las versiones de calidad/audio
  if (state.selectedItem.type === 'movie') {
    if (elements.seriesSeasonBar) elements.seriesSeasonBar.style.display = 'none';
    if (elements.linksCount) {
      elements.linksCount.textContent = `${links.length} enlace${links.length > 1 ? 's' : ''}`;
    }

    elements.linksItemsList.innerHTML = links.map(l => {
      const q = l.q || '1080p';
      const a = l.a || 'Castellano';
      const info = l.i ? `<span class="badge-info">${l.i}</span>` : '';
      return `
        <div class="link-card-row">
          <div class="link-info-badges">
            <span class="badge-quality">${q}</span>
            <span class="badge-audio">${a}</span>
            ${info}
          </div>
          <div class="link-actions-group">
            <a href="${l.u}" target="_blank" rel="noopener noreferrer" class="btn-open-1f">Abrir ↗</a>
            <button type="button" class="btn-copy-url" onclick="copyLinkUrl('${l.u}', this)">📋 Copiar</button>
          </div>
        </div>
      `;
    }).join('');
    return;
  }

  // Si es serie, agrupamos por temporada
  const seasons = [...new Set(links.map(l => l.s))].sort((a, b) => a - b);
  if (!state.activeSeason || !seasons.includes(state.activeSeason)) {
    state.activeSeason = seasons[0];
  }

  // Renderizamos la barra de botones de temporada
  if (elements.seriesSeasonBar) {
    elements.seriesSeasonBar.style.display = seasons.length > 0 ? 'flex' : 'none';
    elements.seriesSeasonBar.innerHTML = seasons.map(s => {
      const activeClass = s === state.activeSeason ? 'active' : '';
      return `<button type="button" class="season-tab-btn ${activeClass}" onclick="selectSeason(${s})">Temporada ${s}</button>`;
    }).join('');
  }

  // Filtramos los episodios de la temporada activa
  const seasonLinks = links.filter(l => l.s === state.activeSeason);
  if (elements.linksCount) {
    elements.linksCount.textContent = `${seasonLinks.length} episodio${seasonLinks.length > 1 ? 's' : ''} (T${state.activeSeason})`;
  }

  elements.linksItemsList.innerHTML = seasonLinks.map(l => {
    const epBadge = `<span class="badge-ep">T${l.s} · E${l.e}</span>`;
    const q = l.q ? `<span class="badge-quality">${l.q}</span>` : '';
    const a = l.a ? `<span class="badge-audio">${l.a}</span>` : '';
    const info = l.i ? `<span class="badge-info">${l.i}</span>` : '';
    return `
      <div class="link-card-row">
        <div class="link-info-badges">
          ${epBadge}
          ${q}
          ${a}
          ${info}
        </div>
        <div class="link-actions-group">
          <a href="${l.u}" target="_blank" rel="noopener noreferrer" class="btn-open-1f">Abrir ↗</a>
          <button type="button" class="btn-copy-url" onclick="copyLinkUrl('${l.u}', this)">📋 Copiar</button>
        </div>
      </div>
    `;
  }).join('');
}

// Cambia la temporada activa seleccionada
window.selectSeason = function(seasonNum) {
  state.activeSeason = seasonNum;
  renderDecryptedLinks();
};

// Hace accesible la función de copiar al ámbito global para el onclick en HTML
window.copyLinkUrl = copyLinkUrl;

// Alterna la visibilidad del panel de enlaces
async function toggleLinksPanel() {
  state.linksOpen = !state.linksOpen;

  if (!state.linksOpen) {
    elements.linksContainer.style.display = 'none';
    elements.btnToggleLinks.classList.remove('active-open');
    elements.btnToggleLinks.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
        <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
      </svg>
      Ver Enlaces
    `;
    return;
  }

  // Si abrimos la sección:
  elements.linksContainer.style.display = 'block';
  elements.btnToggleLinks.classList.add('active-open');
  elements.btnToggleLinks.innerHTML = `
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
      <path d="M7 11V7a5 5 0 0 1 9.9-1"></path>
    </svg>
    Ocultar Enlaces
  `;

  // Comprobamos si la clave guardada en sesión es válida
  let isUnlocked = false;
  if (state.unlockedPassword) {
    const hash = await sha256(state.unlockedPassword);
    if (hash === AUTH_HASH) {
      isUnlocked = true;
    } else {
      state.unlockedPassword = '';
      sessionStorage.removeItem('cinestress_vault_key');
    }
  }

  if (isUnlocked) {
    elements.linksAuthBox.style.display = 'none';
    elements.linksContent.style.display = 'flex';
    renderDecryptedLinks();
  } else {
    elements.linksAuthBox.style.display = 'flex';
    elements.linksContent.style.display = 'none';
    if (elements.authError) elements.authError.style.display = 'none';
    setTimeout(() => {
      if (elements.inputPassword) elements.inputPassword.focus();
    }, 100);
  }
}

// Procesa el desbloqueo mediante contraseña
async function handleUnlock() {
  const entered = (elements.inputPassword.value || '').trim();
  if (!entered) return;

  const enteredHash = await sha256(entered);
  if (enteredHash === AUTH_HASH) {
    state.unlockedPassword = entered;
    sessionStorage.setItem('cinestress_vault_key', entered);
    if (elements.authError) elements.authError.style.display = 'none';
    elements.linksAuthBox.style.display = 'none';
    elements.linksContent.style.display = 'flex';
    renderDecryptedLinks();
  } else {
    if (elements.authError) {
      elements.authError.style.display = 'block';
    }
    if (elements.inputPassword) {
      elements.inputPassword.select();
    }
  }
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

if (elements.btnToggleLinks) {
  elements.btnToggleLinks.addEventListener('click', toggleLinksPanel);
}

if (elements.btnUnlock) {
  elements.btnUnlock.addEventListener('click', handleUnlock);
}

if (elements.inputPassword) {
  elements.inputPassword.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleUnlock();
    }
  });
}

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
