/* MusicWire -- main.js */
const API = 'api/articles.json';
const API_SECTION = '../api/articles.json';

const MONTHS = ['January','February','March','April','May','June',
                'July','August','September','October','November','December'];

function fmtDate(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return `${d.getDate()} ${MONTHS[d.getMonth()]} ${d.getFullYear()}`;
}

function truncate(s, n) {
  return s && s.length > n ? s.slice(0, n - 1) + '…' : (s || '');
}

function articleHref(slug, fromSection) {
  return fromSection ? `../articles/${slug}.html` : `articles/${slug}.html`;
}

async function fetchArticles(apiPath) {
  try {
    const r = await fetch(apiPath);
    if (!r.ok) return null;
    const d = await r.json();
    return d.articles || [];
  } catch { return null; }
}

function setDate(id) {
  const el = document.getElementById(id);
  if (el) {
    const d = new Date();
    el.textContent = `${d.getDate()} ${MONTHS[d.getMonth()]} ${d.getFullYear()}`;
  }
}

function newsItemHTML(a, fromSection) {
  const href = articleHref(a.slug, fromSection);
  const img = a.heroImage
    ? `<div class="news-item-image"><img src="${a.heroImage}" alt="${a.title}" loading="lazy"></div>`
    : `<div class="news-item-image"></div>`;
  return `<div class="news-item">${img}<div>
    <span class="news-item-tag">${(a.type||'NEWS').toUpperCase()}</span>
    <div class="news-item-headline"><a href="${href}">${a.title}</a></div>
    <div class="news-item-meta mono">${fmtDate(a.publishedAt)}</div>
  </div></div>`;
}

function cardHTML(a, fromSection) {
  const href = articleHref(a.slug, fromSection);
  const img = a.heroImage
    ? `<div class="card-image"><img src="${a.heroImage}" alt="${a.title}" loading="lazy"></div>`
    : `<div class="card-image"></div>`;
  const rating = a.rating ? `<div class="card-rating">${a.rating}</div>` : '';
  return `<div class="card">${img}<div class="card-body">
    <div class="card-tag">${(a.type||'').toUpperCase()}</div>
    ${rating}
    <div class="card-headline"><a href="${href}">${a.title}</a></div>
    <div class="card-deck">${truncate(a.deck||'', 120)}</div>
    <div class="card-meta mono">${fmtDate(a.publishedAt)}</div>
  </div></div>`;
}

function fullListHTML(articles, fromSection) {
  if (!articles.length) return '<div class="loading-mono">No content yet.</div>';
  return articles.map(a => {
    const isNews = ['news','breaking'].includes(a.type);
    return isNews ? newsItemHTML(a, fromSection) : cardHTML(a, fromSection);
  }).join('');
}

/* INDEX PAGE */
async function initIndex() {
  setDate('hdr-date');
  const articles = await fetchArticles(API);
  if (!articles || !articles.length) {
    ['news-container','reviews-container','features-container'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.innerHTML = '<div class="loading-mono">No content yet.</div>';
    });
    return;
  }

  // Lead story
  const lead = articles[0];
  const tagEl = document.getElementById('lead-tag');
  const headEl = document.getElementById('lead-headline');
  const deckEl = document.getElementById('lead-deck');
  const dateEl = document.getElementById('lead-date');
  const imgWrap = document.getElementById('lead-img-wrap');

  if (tagEl) tagEl.textContent = (lead.type||'NEWS').toUpperCase();
  if (headEl) headEl.innerHTML = `<a href="${articleHref(lead.slug,false)}" style="color:inherit;text-decoration:none">${lead.title}</a>`;
  if (deckEl) deckEl.textContent = lead.deck || '';
  if (dateEl) dateEl.textContent = fmtDate(lead.publishedAt);
  if (imgWrap && lead.heroImage) {
    imgWrap.innerHTML = `<img src="${lead.heroImage}" alt="${lead.title}" style="width:100%;height:100%;object-fit:cover">`;
  }

  // Breaking banner
  const breaking = articles.find(a => a.breaking);
  if (breaking) {
    const banner = document.getElementById('breaking-banner');
    const text   = document.getElementById('break-text');
    if (banner && text) {
      text.innerHTML = `<a href="${articleHref(breaking.slug,false)}" style="color:inherit">${breaking.title}</a>`;
      banner.style.display = 'block';
    }
  }

  // News feed
  const newsEl = document.getElementById('news-container');
  if (newsEl) {
    const news = articles.filter(a => ['news','breaking'].includes(a.type)).slice(0,5);
    newsEl.innerHTML = news.length ? news.map(a => newsItemHTML(a,false)).join('') : '<div class="loading-mono">No news yet.</div>';
  }

  // Reviews
  const revEl = document.getElementById('reviews-container');
  if (revEl) {
    const reviews = articles.filter(a => ['review','classic-review'].includes(a.type)).slice(0,3);
    revEl.innerHTML = reviews.length ? reviews.map(a => cardHTML(a,false)).join('') : '<div class="loading-mono">No reviews yet.</div>';
  }

  // Features
  const featEl = document.getElementById('features-container');
  if (featEl) {
    const features = articles.filter(a => a.type === 'feature').slice(0,3);
    featEl.innerHTML = features.length ? features.map(a => cardHTML(a,false)).join('') : '<div class="loading-mono">No features yet.</div>';
  }
}

/* SECTION PAGE */
async function initSection(filterFn, containerId, layout) {
  setDate('hdr-date');
  const articles = await fetchArticles(API_SECTION);
  const el = document.getElementById(containerId);
  if (!el) return;
  if (!articles) { el.innerHTML = '<div class="loading-mono">Could not load articles.</div>'; return; }
  const filtered = articles.filter(filterFn);
  if (!filtered.length) { el.innerHTML = '<div class="loading-mono">No content yet.</div>'; return; }
  if (layout === 'list') {
    el.innerHTML = filtered.map(a => newsItemHTML(a, true)).join('');
  } else {
    el.innerHTML = filtered.map(a => cardHTML(a, true)).join('');
  }
}

/* Auto-detect page and initialize */
const path = window.location.pathname;
if (path.endsWith('index.html') || path.endsWith('/') || path === '') {
  document.addEventListener('DOMContentLoaded', initIndex);
} else if (path.includes('news.html')) {
  document.addEventListener('DOMContentLoaded', () =>
    initSection(a => ['news','breaking'].includes(a.type), 'section-container', 'list'));
} else if (path.includes('reviews.html')) {
  document.addEventListener('DOMContentLoaded', () =>
    initSection(a => ['review','classic-review'].includes(a.type), 'section-container', 'grid'));
} else if (path.includes('features.html')) {
  document.addEventListener('DOMContentLoaded', () =>
    initSection(a => a.type === 'feature', 'section-container', 'grid'));
} else if (path.includes('industry.html')) {
  document.addEventListener('DOMContentLoaded', () =>
    initSection(a => a.type === 'industry', 'section-container', 'grid'));
} else if (path.includes('opinion.html')) {
  document.addEventListener('DOMContentLoaded', () =>
    initSection(a => a.type === 'opinion', 'section-container', 'grid'));
} else if (path.includes('live.html')) {
  document.addEventListener('DOMContentLoaded', () =>
    initSection(a => a.type === 'live', 'section-container', 'grid'));
}
