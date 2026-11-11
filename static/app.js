const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const saved = new Map(JSON.parse(localStorage.getItem("seatscout-saved") || "[]").map((item) => [item.id, item]));
const hiddenSeries = new Set();

function toast(message) { const element = $("#toast"); element.textContent = message; element.classList.add("show"); setTimeout(() => element.classList.remove("show"), 1900); }
function persist() { localStorage.setItem("seatscout-saved", JSON.stringify([...saved.values()])); renderSaved(); }
function renderSaved() {
  $("#savedCount").textContent = saved.size;
  $("#savedItems").innerHTML = saved.size ? [...saved.values()].map((item) => `<article class="saved-card"><strong>${item.seller}</strong><span>Section ${item.section} · Row ${item.row}</span><b>$${item.price} each</b></article>`).join("") : '<p class="empty">Punch the heart on a ticket to save it here.</p>';
  $$(".save-offer").forEach((button) => { button.textContent = saved.has(button.closest(".ticket").dataset.id) ? "♥" : "♡"; });
}

$$('.save-offer').forEach((button) => button.addEventListener('click', () => {
  const card = button.closest('.ticket'), id = card.dataset.id;
  if (saved.has(id)) { saved.delete(id); toast('Removed from your ticket drawer'); }
  else { saved.set(id, { id, seller: card.querySelector('.seller-line h3').textContent, section: card.querySelector('.seat-grid span:nth-child(1) b').textContent, row: card.querySelector('.seat-grid span:nth-child(2) b').textContent, price: card.dataset.price }); toast('Saved to your ticket drawer'); }
  persist();
}));
$('#savedButton').onclick = () => $('#savedDrawer').classList.add('open');
$('#closeDrawer').onclick = () => $('#savedDrawer').classList.remove('open');

$$('.tabs [data-category]').forEach((button) => button.onclick = () => {
  $$('.tabs button').forEach((item) => item.classList.remove('active')); button.classList.add('active');
  $$('.event-stub').forEach((card) => { card.hidden = button.dataset.category !== 'All' && card.dataset.category !== button.dataset.category; });
});
$$('.sort-tabs button').forEach((button) => button.onclick = () => {
  $$('.sort-tabs button').forEach((item) => item.classList.remove('active')); button.classList.add('active');
  const cards = $$('.ticket'); cards.sort((a, b) => button.dataset.sort === 'price' ? +a.dataset.price - +b.dataset.price : +b.dataset.score - +a.dataset.score); cards.forEach((card) => $('#ticketList').appendChild(card));
});

$('#quantityButton').onclick = () => $('#quantityDialog').showModal();
$$('.quantity-grid button').forEach((button) => button.onclick = (event) => {
  event.preventDefault(); $$('.quantity-grid button').forEach((item) => item.classList.remove('selected')); button.classList.add('selected');
  $('#quantityButton').textContent = `${button.value} ticket${button.value === '1' ? '' : 's'} together⌄`; setTimeout(() => $('#quantityDialog').close(), 180);
});
const searchCatalog = [
  'The Weeknd', 'Taylor Swift', 'Raptors vs. Celtics', 'Oasis', 'Wicked', 'Phoebe Bridgers',
  'Rogers Centre', 'Scotiabank Arena', 'Rogers Stadium', 'Princess of Wales Theatre',
];
function escapeHTML(value) { return value.replace(/[&<>'"]/g, (char) => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', "'":'&#39;', '"':'&quot;' })[char]); }
function editDistance(a, b) {
  const rows = Array.from({ length: b.length + 1 }, (_, i) => [i]);
  rows[0] = Array.from({ length: a.length + 1 }, (_, i) => i);
  for (let i = 1; i <= b.length; i += 1) for (let j = 1; j <= a.length; j += 1) rows[i][j] = Math.min(rows[i - 1][j] + 1, rows[i][j - 1] + 1, rows[i - 1][j - 1] + (a[j - 1] === b[i - 1] ? 0 : 1));
  return rows[b.length][a.length];
}
function resolveQuery(value) {
  const query = value.trim(), normalized = query.toLowerCase();
  const ranked = searchCatalog.map((label) => ({ label, distance: editDistance(normalized, label.toLowerCase()) })).sort((a, b) => a.distance - b.distance);
  return ranked[0] && ranked[0].distance <= Math.max(2, Math.floor(ranked[0].label.length * .28)) ? ranked[0].label : query;
}
function estimatedPrice(name) { return 95 + [...name].reduce((total, char) => total + char.charCodeAt(0), 0) % 126; }
function marketFromCard(card) {
  return { artist:card.dataset.artist, city:card.dataset.city, venue:card.dataset.venue, date:card.dataset.date, low:+card.dataset.low, change:+card.dataset.change || -5, estimated:card.id === 'estimatedResult' };
}
function generatedHistory(low, change) {
  const factor = 1 + Math.abs(change) / 100, steps = [1.12,1.09,1.1,1.06,1.04,1.05,1.02,1];
  const series = (multiple) => steps.map((step) => Math.round(low * multiple * step * factor / factor));
  return { labels:['Oct 12','Oct 16','Oct 20','Oct 24','Oct 28','Nov 1','Nov 5','Today'], low:series(1), median:series(1.28), official:series(1.72), resale:series(1.14) };
}
function setActiveMarket(eventData, scroll = false) {
  const { artist, city, venue, date, low, change, estimated } = eventData;
  $$('.event-stub').forEach((card) => card.classList.toggle('active-market', card.dataset.artist === artist));
  $('#marketModeLabel').textContent = estimated ? 'ESTIMATED MARKET PREVIEW' : 'MARKET BOARD';
  $('#marketEventTitle').textContent = `${artist} — ${city}`;
  $('#marketEventSubtitle').textContent = estimated ? 'Projected ticket market' : `${artist} ticket market`;
  $('#marketEventMeta').textContent = `${venue} · ${date}${estimated ? '' : ' · local time TBA'}`;
  window.SEATSCOUT_HISTORY = generatedHistory(low, change);
  const current = Object.fromEntries(['low','median','official','resale'].map((key) => [key, window.SEATSCOUT_HISTORY[key].at(-1)]));
  $$('.chart-legend button').forEach((button) => { button.querySelector('b').textContent = `$${current[button.dataset.series]}`; });
  $('#marketChange').textContent = `${change <= 0 ? '↓' : '↑'} ${Math.abs(change).toFixed(1)}%`;
  $('#marketLowest').textContent = `$${Math.max(1, Math.round(low * .96))}`;
  $('#marketSignal').textContent = change < -6 ? 'Good time to buy' : change > 2 ? 'Prices are rising' : 'Market is steady';

  const zonePrices = { '200 Level':low, '100 Level':Math.round(low * 1.23), Floor:Math.round(low * 2.35), Accessible:Math.round(low * 1.29) };
  Object.entries(zonePrices).forEach(([name, price]) => {
    const data = zoneData[name]; data.price = price; data.median = Math.round(price * 1.22); data.movement = `${change <= 0 ? '↓' : '↑'} ${Math.abs(change).toFixed(1)}%`; data.rows = data.rows.map(([row], index) => [row, Math.round(price * (1 + index * .09))]);
    $$(`.zone-trigger[data-zone="${name}"]`).forEach((trigger) => { trigger.dataset.price = price; trigger.setAttribute('aria-label', `${name}, tickets from $${price}`); trigger.querySelector('span') ? trigger.querySelector('span').textContent = `$${price}` : null; const bold = trigger.querySelector('b'); if (bold) bold.textContent = `$${price}+`; });
  });

  const sellerMultipliers = [1.14,1.18,1.22,1.72,1.3];
  $$('.ticket').forEach((ticket, index) => {
    const total = Math.round(low * sellerMultipliers[index]), fees = Math.max(12, Math.round(total * .08)), base = total - fees;
    ticket.dataset.price = total; ticket.querySelector('.ticket-stub strong').textContent = `$${total}`; ticket.querySelector('.ticket-stub small').textContent = `each · $${base} + $${fees} fees`;
  });
  $$('.seller-strip ol li b').forEach((price, index) => { price.textContent = `$${Math.round(low * sellerMultipliers[index])}`; });
  $('#zone-details').hidden = true;
  drawChart(+$('.range-tabs .active').dataset.range);
  if (scroll) $('#market').scrollIntoView({behavior:'smooth',block:'start'});
}
function showCatalogResults(query) {
  const resolved = resolveQuery(query), needle = resolved.toLowerCase();
  const cards = $$('.event-stub:not(#estimatedResult)'), matches = cards.filter((card) => card.textContent.toLowerCase().includes(needle));
  if (!matches.length) return false;
  $('#estimatedResult')?.remove();
  cards.forEach((card) => { card.hidden = !matches.includes(card); });
  const corrected = resolved.toLowerCase() !== query.trim().toLowerCase(), summary = $('#searchSummary');
  summary.hidden = false;
  summary.innerHTML = `<div><span class="label">SEARCH RESULT</span><strong>${corrected ? `Showing “${escapeHTML(resolved)}” for “${escapeHTML(query.trim())}”` : `${matches.length} matching event${matches.length === 1 ? '' : 's'}`}</strong><small>Matched across artists, events, teams, cities, and venues</small></div><button type="button" id="clearSearch">Clear</button>`;
  $('#clearSearch').onclick = clearSearchResults;
  setActiveMarket(marketFromCard(matches[0]));
  toast(corrected ? `Corrected to ${resolved}` : `${matches.length} matching event${matches.length === 1 ? '' : 's'}`);
  return true;
}
function clearSearchResults() { $('#searchSummary').hidden = true; $('#estimatedResult')?.remove(); $$('.event-stub').forEach((card) => { card.hidden = false; }); }
function showEstimatedResult(query, city) {
  const artist = resolveQuery(query), corrected = artist.toLowerCase() !== query.trim().toLowerCase(), price = estimatedPrice(artist);
  const safeArtist = escapeHTML(artist), safeQuery = escapeHTML(query.trim()), safeCity = escapeHTML(city);
  const summary = $('#searchSummary');
  summary.hidden = false;
  summary.innerHTML = `<div><span class="label">SEARCH RESULT</span><strong>${corrected ? `Showing “${safeArtist}” for “${safeQuery}”` : `Showing “${safeArtist}”`}</strong><small>Live inventory unavailable · displaying a market estimate</small></div><button type="button" id="clearSearch">Clear</button>`;
  $$('.event-stub').forEach((card) => { card.hidden = true; });
  $('#estimatedResult')?.remove();
  $('#eventRail').insertAdjacentHTML('afterbegin', `<article class="event-stub estimated-result" id="estimatedResult" tabindex="0" role="button" data-category="Concerts" data-artist="${safeArtist}" data-city="${safeCity}" data-venue="Venue TBA" data-date="Date TBA" data-low="${price}" data-change="-5"><div class="event-date">DATE TBA</div><h3>${safeArtist}</h3><p>${safeCity} · venue and date to be confirmed</p><div><strong>estimated from $${price}</strong><span class="estimate-badge">ESTIMATE</span><button class="save-event" aria-label="Save ${safeArtist}">♡</button></div></article>`);
  setActiveMarket(marketFromCard($('#estimatedResult')));
  $('#clearSearch').onclick = clearSearchResults;
  toast(corrected ? `Corrected to ${artist} · estimated result shown` : 'Estimated market result shown');
}
$('#searchForm').onsubmit = async (event) => {
  event.preventDefault(); const query = $('#searchInput').value.trim(), city = $('#citySelect').value;
  if (!query) { toast('Enter an artist, event, or venue'); return; }
  toast('Searching official and resale sources…');
  try {
    const response = await fetch(`/api/search?q=${encodeURIComponent(query)}&city=${encodeURIComponent(city)}`);
    if (!response.ok) throw new Error('Static preview');
    const data = await response.json();
    if (!showCatalogResults(query)) showEstimatedResult(resolveQuery(query), city);
    if (data.events.length && data.mode === 'live') toast(`${data.events.length} live events found`);
  } catch { if (!showCatalogResults(query)) showEstimatedResult(query, city); }
  $('#discover').scrollIntoView();
};
$$('.deal-button').forEach((button) => button.onclick = () => toast('Seller links activate when live marketplace feeds are connected'));
$('.alert-btn').onclick = () => toast('Price watch saved on this device');

function drawChart(range = 30) {
  const svg = $('#priceChart'), data = window.SEATSCOUT_HISTORY;
  if (!svg || !data || !Array.isArray(data.labels)) return;
  const W = 760, H = 260, padding = { l: 48, r: 18, t: 18, b: 34 };
  const count = range === 7 ? 4 : data.labels.length, start = Math.max(0, data.labels.length - count), labels = data.labels.slice(start);
  const visibleValues = ['low','median','official','resale'].filter((key) => !hiddenSeries.has(key)).flatMap((key) => data[key].slice(start));
  const rawMin = Math.min(...visibleValues), rawMax = Math.max(...visibleValues), spread = Math.max(40, rawMax - rawMin), min = Math.max(0, Math.floor((rawMin - spread * .12) / 10) * 10), max = Math.ceil((rawMax + spread * .12) / 10) * 10;
  const x = (index) => padding.l + index * (W - padding.l - padding.r) / Math.max(1, labels.length - 1);
  const y = (value) => padding.t + (max - value) * (H - padding.t - padding.b) / (max - min);
  let markup = '';
  Array.from({length:7}, (_, index) => Math.round((min + (max-min) * index / 6) / 10) * 10).forEach((value) => { markup += `<line x1="${padding.l}" y1="${y(value)}" x2="${W-padding.r}" y2="${y(value)}" stroke="rgba(28,33,27,.16)"/><text x="4" y="${y(value)+4}" font-size="10" font-family="DM Mono">$${value}</text>`; });
  labels.forEach((label, index) => { markup += `<text x="${x(index)}" y="${H-8}" text-anchor="middle" font-size="9" font-family="DM Mono">${label}</text>`; });
  [['low','#e0a82e','4 5'],['median','#6f7645',''],['official','#8f1f25','8 5'],['resale','#67151a','']].forEach(([key,color,dash]) => {
    if (hiddenSeries.has(key)) return;
    const values = data[key].slice(start), points = values.map((value,index) => `${x(index)},${y(value)}`).join(' ');
    markup += `<polyline points="${points}" fill="none" stroke="${color}" stroke-width="3" stroke-dasharray="${dash}" stroke-linecap="round" stroke-linejoin="round"/>`;
    values.forEach((value,index) => { markup += `<circle class="chart-point" tabindex="0" data-label="${labels[index]}" data-series="${key}" data-value="${value}" cx="${x(index)}" cy="${y(value)}" r="6" fill="${color}" stroke="#fff8e9" stroke-width="3"/>`; });
  });
  svg.innerHTML = markup;
  $$('.chart-point').forEach((point) => {
    const show = () => { const tooltip = $('#chartTooltip'); tooltip.innerHTML = `<small>${point.dataset.label}</small><strong>${point.dataset.series[0].toUpperCase()+point.dataset.series.slice(1)} · $${point.dataset.value}</strong>`; tooltip.classList.add('visible'); };
    point.addEventListener('mouseenter', show); point.addEventListener('focus', show); point.addEventListener('mouseleave', () => $('#chartTooltip').classList.remove('visible')); point.addEventListener('blur', () => $('#chartTooltip').classList.remove('visible'));
  });
}
$$('.range-tabs button').forEach((button) => button.onclick = () => { $$('.range-tabs button').forEach((item) => item.classList.remove('active')); button.classList.add('active'); drawChart(+button.dataset.range); });
$$('.chart-legend button').forEach((button) => button.onclick = () => { const series = button.dataset.series; hiddenSeries.has(series) ? hiddenSeries.delete(series) : hiddenSeries.add(series); button.classList.toggle('muted', hiddenSeries.has(series)); drawChart(+$('.range-tabs .active').dataset.range); });

const zoneData = {
  'Floor': { price:612, median:734, movement:'↓ 4.8%', count:11, rows:[['A',612],['B',648],['C',701],['D',759]] },
  '100 Level': { price:276, median:341, movement:'↓ 9.6%', count:24, rows:[['H',276],['J',289],['K',310],['M',344]] },
  '200 Level': { price:224, median:298, movement:'↓ 13.2%', count:38, rows:[['3',224],['7',241],['11',267],['15',298]] },
  'Accessible': { price:289, median:326, movement:'↓ 7.1%', count:6, rows:[['A',289],['B',304],['C',318],['D',326]] },
};
function previewZone(trigger) {
  const tooltip = $('#zoneTooltip'); tooltip.innerHTML = `<small>${trigger.dataset.zone.toUpperCase()}</small><strong>From $${trigger.dataset.price}</strong><span>${trigger.dataset.count} listings · click for details</span>`; tooltip.classList.add('visible');
  $$('.zone-trigger').forEach((item) => item.classList.toggle('previewing', item.dataset.zone === trigger.dataset.zone));
}
function clearZonePreview() { $('#zoneTooltip').classList.remove('visible'); $$('.zone-trigger').forEach((item) => item.classList.remove('previewing')); }
function openZoneDetails(zone) {
  const data = zoneData[zone] || zoneData['200 Level'];
  $('#zoneDetailTitle').textContent = zone; $('#zoneDetailSummary').textContent = `${data.count} matching listings from $${data.price}, including estimated fees.`;
  $('#zoneCurrentLow').textContent = `$${data.price}`; $('#zoneMedian').textContent = `$${data.median}`; $('#zoneMovement').textContent = data.movement; $('#zoneListingCount').textContent = data.count;
  $('#zoneRowBars').innerHTML = data.rows.map(([row,price]) => `<div><span>Row ${row}</span><i style="--bar:${Math.min(100,price/data.median*70)}%"></i><b>$${price}</b></div>`).join('');
  const matching = $$('.ticket').filter((ticket) => zone === 'Floor' ? +ticket.dataset.price > 500 : zone === '100 Level' ? ['118','121','124','130'].includes(ticket.querySelector('.seat-grid span b').textContent) : true).slice(0,3);
  $('#zoneMatches').innerHTML = matching.map((ticket) => `<button data-ticket="${ticket.dataset.id}"><span>${ticket.querySelector('.seller-line h3').textContent}</span><b>$${ticket.dataset.price}</b><small>${ticket.querySelector('.seat-grid').innerText.replaceAll('\n',' · ')}</small></button>`).join('') || '<p>No matching demo listings in this zone yet.</p>';
  const panel = $('#zone-details'); panel.hidden = false; history.pushState(null,'','#zone-details'); panel.scrollIntoView({behavior:'smooth',block:'start'}); setTimeout(() => panel.focus({preventScroll:true}),450);
}
$$('.zone-trigger').forEach((trigger) => { trigger.addEventListener('mouseenter', () => previewZone(trigger)); trigger.addEventListener('focus', () => previewZone(trigger)); trigger.addEventListener('mouseleave', clearZonePreview); trigger.addEventListener('blur', clearZonePreview); trigger.addEventListener('click', () => openZoneDetails(trigger.dataset.zone)); });
$('#closeZoneDetails').onclick = () => { $('#zone-details').hidden = true; history.replaceState(null,'','#market'); $('.venue-map').scrollIntoView({behavior:'smooth',block:'center'}); };

$('#eventRail').addEventListener('click', (event) => {
  if (event.target.closest('button')) return;
  const card = event.target.closest('.event-stub'); if (card) setActiveMarket(marketFromCard(card), true);
});
$('#eventRail').addEventListener('keydown', (event) => {
  if (!['Enter',' '].includes(event.key) || event.target.closest('button')) return;
  const card = event.target.closest('.event-stub'); if (card) { event.preventDefault(); setActiveMarket(marketFromCard(card), true); }
});

drawChart();
renderSaved();
