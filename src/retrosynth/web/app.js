// retrosynth studio — browser side. Audio is rendered by the Python server; this file
// wires the header, song list, the two views (visual tracks / code), playback,
// waveform, analysis and the on-screen keyboard.
'use strict';

const $ = s => document.querySelector(s);
const TOKEN = document.querySelector('meta[name="studio-token"]').content;
const SR = 44100;
const DRAFT_KEY = 'retrosynth.draft';

const CODE_TEMPLATE = `"""My song — C major, 100 bpm. Press Ctrl+Enter to hear it."""

from retrosynth import *

s = Song(bpm=100, bars=8)
chart = progression("C:4 Am:4 F:4 G:4  C:4 Am:4 F:4 G:4")

for bar, ch in enumerate(chart):
    c = ch.notes
    pad(s, bar, c, 4, gain=0.07, wet=0.5)                                   # string pad
    s.put(inst.bass(midi(c[0] - 12), s.beat * 1.8), s.at(bar, 0), gain=0.35, wet=0.1)
    s.put(inst.bass(midi(c[2] - 12), s.beat * 1.8), s.at(bar, 2), gain=0.28, wet=0.1)
    arpeggio(s, bar, c, [0, 1, 2, 1], step=1, gain=0.12, pan=0.3)          # harp, quarter notes
    s.put(inst.kick(), s.at(bar), gain=0.45, wet=0.05)
    drum_pattern(s, bar, ".x.x.x.x", "hihat", gain=0.06, pan=-0.3)

s.melody("flute", 0, mel("""
    E5:1 G5:1 C6:2   C6:1 B5:1 A5:2   A5:1 F5:1 C6:1.5 A5:0.5   G5:4
    E5:1 G5:1 C6:2   D6:1 C6:1 A5:2   F5:1 A5:1 G5:1 F5:1       E5:2 D5:2
"""), gain=0.25, wet=0.4)

song = s.render(reverb_size=1.2, loudness=0.12)   # room size, target loudness
`;

// ── State ───────────────────────────────────────────────────────────────────
// kind: what the current song is ("visual" project or hand-written "code");
// view: which panel is on screen. A visual song can be *viewed* as code (read-only).
const state = { kind: 'visual', view: 'visual', current: null, dirty: false, info: null, visual: null };

// ── HTTP helpers ────────────────────────────────────────────────────────────
async function api(path, { method = 'GET', body } = {}) {
  const res = await fetch(path, {
    method,
    headers: { 'X-Studio-Token': TOKEN, ...(body ? { 'Content-Type': 'application/json' } : {}) },
    body: body ? JSON.stringify(body) : undefined,
  });
  const type = res.headers.get('content-type') || '';
  const data = type.includes('application/json') ? await res.json() : await res.arrayBuffer();
  if (!res.ok) {
    const err = new Error((data && data.error) || (data && data.detail && JSON.stringify(data.detail)) || res.statusText);
    err.line = data && data.line;
    throw err;
  }
  return data;
}

function status(text, cls = '') { const e = $('#status'); e.textContent = text; e.className = cls; e.title = text; }

// ── Code editor (CodeMirror, or a plain textarea if the CDN is unreachable) ──
let ed;
if (window.CodeMirror) {
  const cm = CodeMirror($('#editorBox'), {
    value: '', mode: 'python', lineNumbers: true, matchBrackets: true, autoCloseBrackets: true, indentUnit: 4, tabSize: 4,
    extraKeys: {
      'Ctrl-Enter': () => render(), 'Cmd-Enter': () => render(), 'Ctrl-S': () => save(), 'Cmd-S': () => save(),
      'Ctrl-/': 'toggleComment', 'Cmd-/': 'toggleComment',
      Tab: c => c.somethingSelected() ? c.indentSelection('add') : c.replaceSelection('    '),
    },
  });
  let mark = null, silent = false;
  ed = {
    get: () => cm.getValue(),
    set: v => { silent = true; cm.setValue(v); cm.clearHistory(); silent = false; },
    insert: t => { cm.replaceSelection(t); cm.focus(); },
    mark: n => { ed.clear(); mark = cm.addLineClass(n - 1, 'background', 'error-line'); cm.scrollIntoView({ line: n - 1, ch: 0 }, 80); },
    clear: () => { if (mark) cm.removeLineClass(mark, 'background', 'error-line'); mark = null; },
    onChange: f => cm.on('change', () => { if (!silent) f(); }),
    readOnly: ro => cm.setOption('readOnly', ro),
    refresh: () => cm.refresh(),
  };
} else {
  const ta = document.createElement('textarea'); ta.className = 'plain'; ta.spellcheck = false; $('#editorBox').appendChild(ta);
  ed = {
    get: () => ta.value, set: v => { ta.value = v; }, insert: t => ta.setRangeText(t, ta.selectionStart, ta.selectionEnd, 'end'),
    mark: () => { }, clear: () => { }, onChange: f => ta.addEventListener('input', f),
    readOnly: ro => { ta.readOnly = ro; }, refresh: () => { },
  };
}

// ── Views ───────────────────────────────────────────────────────────────────
async function setView(view) {
  state.view = view;
  $('#viewVisual').classList.toggle('on', view === 'visual');
  $('#viewCode').classList.toggle('on', view === 'code');
  document.body.dataset.view = view;
  $('#visual').hidden = !(view === 'visual' && state.kind === 'visual');
  $('#notVisual').hidden = !(view === 'visual' && state.kind === 'code');
  $('#codeView').hidden = view !== 'code';
  $('#codeBanner').hidden = !(view === 'code' && state.kind === 'visual');
  ed.readOnly(view === 'code' && state.kind === 'visual');
  if (view === 'code' && state.kind === 'visual') {
    try { ed.set((await api('/api/project/code', { method: 'POST', body: { project: state.visual.project } })).code); }
    catch (e) { status(e.message, 'bad'); }
  }
  if (view === 'code') ed.refresh();
  saveDraft();
}
$('#viewVisual').onclick = () => setView('visual');
$('#viewCode').onclick = () => setView('code');
$('#backToCode').onclick = () => setView('code');
$('#startVisual').onclick = () => openNewDialog();
$('#editAsCode').onclick = () => {
  if (!confirm(t('v.editAsCode.confirm'))) return;
  // drop the embedded project so the song is no longer treated as a visual one
  ed.set(ed.get().split('\n').filter(l => !l.startsWith('# retrosynth-project: ')).join('\n'));
  state.kind = 'code'; state.dirty = true;
  setView('code');
};

// ── Audio playback ──────────────────────────────────────────────────────────
let ctx, master, buffer = null, source = null, startedAt = 0, offset = 0, playing = false, looping = true;
function audio() {
  if (!ctx) {
    ctx = new AudioContext({ sampleRate: SR });
    master = ctx.createGain(); master.gain.value = +$('#volume').value; master.connect(ctx.destination);
  }
  if (ctx.state === 'suspended') ctx.resume();
  return ctx;
}
$('#volume').oninput = e => { if (master) master.gain.value = +e.target.value; };

function position() {
  if (!buffer) return 0;
  if (!playing) return offset;
  const tm = offset + ctx.currentTime - startedAt;
  return looping ? tm % buffer.duration : Math.min(tm, buffer.duration);
}
function stop() {
  if (source) { try { source.stop(); } catch { } source.disconnect(); source = null; }
  if (playing) offset = position();
  playing = false;
}
function play(from = 0) {
  if (!buffer) return;
  stop(); audio();
  source = ctx.createBufferSource(); source.buffer = buffer; source.loop = looping; source.connect(master);
  offset = Math.max(0, Math.min(from, buffer.duration - 0.01)); startedAt = ctx.currentTime;
  source.start(0, offset); playing = true;
  const mine = source;
  source.onended = () => { if (source === mine && !looping) { playing = false; offset = 0; } };
}
$('#stop').onclick = () => { stop(); offset = 0; };
$('#loop').onclick = e => { looping = !looping; e.currentTarget.classList.toggle('on', looping); if (source) source.loop = looping; };

// ── Render ──────────────────────────────────────────────────────────────────
let renderSeq = 0;
const songName = () => $('#name').value.trim() || 'untitled';
const songBody = () => state.kind === 'visual'
  ? { name: songName(), project: state.visual.project }
  : { name: songName(), code: ed.get() };

/** Render the current song. ``keepPosition``: continue playing from the same spot (live edits). */
async function render({ keepPosition = false } = {}) {
  const seq = ++renderSeq;
  audio();
  status(t('st.rendering')); ed.clear(); $('#error').hidden = true;
  try {
    const r = await api('/api/render', { method: 'POST', body: songBody() });
    const wav = await api(`/api/audio/${r.id}`);
    const decoded = await ctx.decodeAudioData(wav);
    if (seq !== renderSeq) return;  // a newer render superseded this one
    const at = keepPosition && playing ? position() % decoded.duration : 0;
    buffer = decoded;
    status(t('st.ready', { d: r.analysis.duration.toFixed(1), s: r.seconds.toFixed(2) }), 'ok');
    showLog(r.log);
    showAnalysis(r.analysis); drawWave(); play(at);
  } catch (e) {
    if (seq !== renderSeq) return;
    status(t('st.error') + ': ' + e.message, 'bad');
    if (state.kind === 'code') {
      $('#error').hidden = false;
      $('#error').textContent = (e.line ? t('st.line', { n: e.line }) : '') + e.message;
      if (e.line) { ed.mark(e.line); if (state.view !== 'code') setView('code'); }
    }
  }
}
$('#render').onclick = () => render();

let liveTimer = null;
function onVisualChange() {
  state.dirty = true; saveDraft();
  if (state.visual.live && playing) {
    clearTimeout(liveTimer);
    liveTimer = setTimeout(() => render({ keepPosition: true }), 400);
  }
}

function showLog(text) { $('#log').hidden = !text; $('#log').textContent = text || ''; }

// ── Analysis ────────────────────────────────────────────────────────────────
let lastAnalysis = null;
function fmtTime(s) { return `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`; }
function showAnalysis(a) {
  lastAnalysis = a;
  if (!a) return;
  const row = (k, v, c = '') => `<div><span>${t(k)}</span><b class="${c}">${v}</b></div>`;
  $('#analysis').innerHTML =
    row('an.duration', `${fmtTime(a.duration)}.${Math.floor((a.duration % 1) * 10)}`) +
    row('an.loudness', a.rms_db.toFixed(1) + ' dB', a.rms_db > -12 || a.rms_db < -24 ? 'warn' : 'ok') +
    row('an.peak', a.peak_db.toFixed(1) + ' dB', a.peak_db > -0.5 ? 'bad' : a.peak_db > -2 ? 'warn' : 'ok') +
    row('an.clipping', a.clipped ? t('an.clipped', { n: a.clipped }) : t('an.none'), a.clipped > 100 ? 'bad' : a.clipped ? 'warn' : 'ok') +
    row('an.seam', a.seam_clean ? t('an.clean') : t('an.audible', { n: a.seam_ratio.toFixed(0) }), a.seam_clean ? 'ok' : a.seam_ratio < 12 ? 'warn' : 'bad') +
    row('an.samples', a.samples.toLocaleString(LANG));
}

// ── Waveform and playhead ───────────────────────────────────────────────────
const canvas = $('#wave'), g = canvas.getContext('2d');
let waveImage = null;
function drawWave() {
  const w = canvas.width = canvas.clientWidth * devicePixelRatio, h = canvas.height = canvas.clientHeight * devicePixelRatio;
  g.clearRect(0, 0, w, h);
  if (!buffer) return;
  const L = buffer.getChannelData(0), R = buffer.getChannelData(1), step = L.length / w, mid = h / 2;
  g.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--gold');
  for (let x = 0; x < w; x++) {
    let lo = 1, hi = -1;
    const a = Math.floor(x * step), b = Math.min(L.length, Math.floor((x + 1) * step));
    for (let i = a; i < b; i += 4) { const v = (L[i] + R[i]) / 2; if (v < lo) lo = v; if (v > hi) hi = v; }
    g.fillRect(x, mid - hi * mid * 0.95, 1, Math.max(1, (hi - lo) * mid * 0.95));
  }
  waveImage = g.getImageData(0, 0, w, h);
}
(function frame() {
  if (buffer && waveImage) {
    g.putImageData(waveImage, 0, 0);
    const p = position(), x = p / buffer.duration * canvas.width;
    g.fillStyle = 'rgba(16,13,23,.55)'; g.fillRect(0, 0, x, canvas.height);
    g.fillStyle = '#fff'; g.fillRect(x, 0, 2 * devicePixelRatio, canvas.height);
    $('#time').textContent = `${fmtTime(p)} / ${fmtTime(buffer.duration)}`;
  }
  if (state.visual) state.visual.setPlayhead(playing && state.kind === 'visual' ? position() : null);
  requestAnimationFrame(frame);
})();
canvas.onclick = e => { if (!buffer) return; const r = canvas.getBoundingClientRect(); play((e.clientX - r.left) / r.width * buffer.duration); };
addEventListener('resize', drawWave);

// ── Single notes (keyboard, previews in the visual editor) ──────────────────
const noteCache = new Map();
async function playNote(instrument, pitch, seconds, gain = 0.5) {
  audio();
  const key = `${instrument}|${pitch}|${seconds.toFixed(3)}`;
  let b = noteCache.get(key);
  if (!b) {
    try {
      const wav = await api(`/api/note?instrument=${encodeURIComponent(instrument)}&pitch=${pitch}&duration=${seconds.toFixed(3)}`);
      b = await ctx.decodeAudioData(wav);
    } catch (e) { return status(e.message, 'bad'); }
    noteCache.set(key, b);
    if (noteCache.size > 400) noteCache.delete(noteCache.keys().next().value);
  }
  const s = ctx.createBufferSource(), gn = ctx.createGain();
  gn.gain.value = gain; s.buffer = b; s.connect(gn).connect(master); s.start();
}

// ── Song list ───────────────────────────────────────────────────────────────
let songs = { mine: [], examples: [] }, tab = 'mine';
async function loadSongs() { songs = await api('/api/songs'); drawList(); }
function drawList() {
  const q = $('#search').value.trim().toLowerCase();
  const items = songs[tab].filter(s => !q || s.name.toLowerCase().includes(q) || s.description.toLowerCase().includes(q));
  const list = $('#list'); list.innerHTML = '';
  if (!items.length) list.append(Object.assign(document.createElement('p'), { className: 'empty', textContent: tab === 'mine' && !q ? t('empty.mine') : t('empty.none') }));
  for (const s of items) {
    const row = document.createElement('div'); row.className = 'song' + (state.current === `${tab}:${s.name}` ? ' sel' : '');
    row.tabIndex = 0;
    const info = document.createElement('div');
    const b = document.createElement('b'); b.textContent = (s.project ? '🎛 ' : '</> ') + s.name; info.append(b);
    const sm = document.createElement('small'); sm.textContent = s.description || new Date(s.modified * 1000).toLocaleString(LANG); info.append(sm);
    row.append(info);
    row.onclick = () => openSong(s, tab);
    row.onkeydown = e => { if (e.key === 'Enter') openSong(s, tab); };
    if (tab === 'mine') {
      const x = document.createElement('button'); x.className = 'x'; x.textContent = '✕'; x.title = t('delete.title'); x.setAttribute('aria-label', `${t('delete.title')}: ${s.name}`);
      x.onclick = async ev => {
        ev.stopPropagation();
        if (!confirm(t('delete.confirm', { name: s.name }))) return;
        await api('/api/delete', { method: 'POST', body: { name: s.name } }); loadSongs();
      };
      row.append(x);
    }
    list.append(row);
  }
}
const confirmDiscard = () => !state.dirty || confirm(t('unsaved'));

function loadSong({ kind, project = null, code = '', name = '', current = null, view = null }) {
  state.kind = kind; state.current = current; state.dirty = false;
  $('#name').value = name;
  if (kind === 'visual') state.visual.load(project); else ed.set(code);
  ed.clear(); $('#error').hidden = true;
  stop(); buffer = null; waveImage = null; g.clearRect(0, 0, canvas.width, canvas.height); $('#analysis').innerHTML = '';
  drawList();
  setView(view || kind);  // also saves the draft, with the name already in place
}
function openSong(s, origin) {
  if (!confirmDiscard()) return;
  loadSong({
    kind: s.project ? 'visual' : 'code', project: s.project, code: s.code,
    name: origin === 'examples' ? `${s.name}_copy` : s.name,  // examples are read-only templates
    current: `${origin}:${s.name}`,
  });
  status(t('st.opened', { name: s.name }));
}
document.querySelectorAll('#songs .tabs button').forEach(b => b.onclick = () => selectTab(b.dataset.tab));
function selectTab(name) {
  tab = name;
  document.querySelectorAll('#songs .tabs button').forEach(x => x.classList.toggle('on', x.dataset.tab === name));
  drawList();
}
$('#search').oninput = drawList;

// New song: pick a style
function openNewDialog() {
  if (!confirmDiscard()) return;
  const cards = $('#presetCards'); cards.innerHTML = '';
  for (const p of state.info.presets) {
    const b = document.createElement('button'); b.className = 'card';
    b.innerHTML = `<span class="card-icon" aria-hidden="true">${p.icon}</span><b></b><small></small>`;
    b.querySelector('b').textContent = p.name[LANG] || p.name.en;
    b.querySelector('small').textContent = p.description[LANG] || p.description.en;
    b.onclick = () => {
      $('#newDialog').close();
      loadSong({ kind: 'visual', project: p.project, name: `my_${p.id}` });
      render();
    };
    cards.append(b);
  }
  $('#newDialog').showModal();
}
$('#new').onclick = openNewDialog;
$('#newCancel').onclick = () => $('#newDialog').close();
$('#newCode').onclick = () => { $('#newDialog').close(); loadSong({ kind: 'code', code: CODE_TEMPLATE, name: 'my_song' }); };

// Save and export
function validName() {
  const n = $('#name').value.trim();
  if (!/^[A-Za-z0-9_-]{1,60}$/.test(n)) { status(t('st.badName'), 'bad'); $('#name').focus(); return null; }
  return n;
}
async function save() {
  const n = validName(); if (!n) return;
  try {
    const r = await api('/api/save', { method: 'POST', body: { ...songBody(), name: n } });
    state.dirty = false; state.current = 'mine:' + n; status(t('st.saved', { path: r.path }), 'ok');
    await loadSongs(); selectTab('mine'); saveDraft();
  } catch (e) { status(e.message, 'bad'); }
}
$('#save').onclick = save;
$('#export').onclick = async () => {
  const n = validName(); if (!n) return;
  status(t('st.exporting'));
  try {
    const r = await api('/api/export', { method: 'POST', body: { ...songBody(), name: n } });
    status(`${r.warning ? r.warning + ' · ' : ''}${t('st.exported', { files: r.files.join(', ') })}`, r.warning ? '' : 'ok');
  } catch (e) { status(t('st.exportFailed', { msg: e.message }), 'bad'); }
};
$('#openOutput').onclick = () => api('/api/open-output', { method: 'POST' })
  .then(r => { if (!r.opened) status(r.folder); })
  .catch(e => status(e.message, 'bad'));

// Draft autosave (in case the tab is closed by accident). Saved *after* every change
// to the song, name or view, so the stored name always matches the stored song.
function saveDraft() {
  if (!state.visual) return;
  const draft = {
    kind: state.kind, view: state.view, name: $('#name').value, current: state.current, dirty: state.dirty,
    project: state.kind === 'visual' ? state.visual.project : null, code: state.kind === 'code' ? ed.get() : null,
  };
  try { localStorage.setItem(DRAFT_KEY, JSON.stringify(draft)); } catch { }
}
ed.onChange(() => { if (state.kind === 'code') { state.dirty = true; saveDraft(); } });
$('#name').oninput = saveDraft;

// ── On-screen keyboard (code view) ──────────────────────────────────────────
const NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
const noteName = m => NAMES[m % 12] + (Math.floor(m / 12) - 1);
const KEYS = 'zsxdcvgbhnjm,'.split('').concat('q2w3er5t6y7ui'.split(''));  // semitones 0…12 and 12…24
const keyOffset = k => { const i = KEYS.indexOf(k); return i < 0 ? null : i < 13 ? i : i - 1; };

function drawPiano() {
  const piano = $('#piano'); piano.innerHTML = '';
  const base = (+$('#octave').value + 1) * 12, whites = [0, 2, 4, 5, 7, 9, 11], total = 25;
  const width = 100 / [...Array(total).keys()].filter(i => whites.includes(i % 12)).length;
  let x = 0;
  for (let i = 0; i < total; i++) {
    const m = base + i, white = whites.includes(i % 12), d = document.createElement('div');
    const label = (i < 12 ? KEYS[i] : KEYS[i + 1]) || '';
    d.className = 'key ' + (white ? 'w' : 'b'); d.dataset.m = m; d.title = noteName(m);
    d.innerHTML = `<em>${label === ',' ? '' : label.toUpperCase()}</em>${white && i % 12 === 0 ? noteName(m) : ''}`;
    if (white) { d.style.left = x * width + '%'; d.style.width = width + '%'; x++; }
    else { d.style.left = (x - 0.32) * width + '%'; d.style.width = width * 0.64 + '%'; }
    d.onpointerdown = e => { e.preventDefault(); press(m); };
    piano.append(d);
  }
}
let recording = false;
function press(m) {
  playNote($('#instrument').value, m, Math.max(0.12, +$('#length').value * 60 / +$('#bpm').value));
  const k = document.querySelector(`.key[data-m="${m}"]`);
  if (k) { k.classList.add('down'); setTimeout(() => k.classList.remove('down'), 160); }
  if (recording) write(noteName(m));
}
function write(token) {
  const ta = $('#melody');
  ta.value = (ta.value.trimEnd() + ' ' + token + ':' + $('#length').value).trimStart();
  ta.scrollTop = ta.scrollHeight;
}
$('#record').onclick = e => {
  recording = !recording;
  e.currentTarget.classList.toggle('on', recording);
  e.currentTarget.textContent = t(recording ? 'kb.recording' : 'kb.record');
};
$('#rest').onclick = () => write('r');
$('#undo').onclick = () => { const ta = $('#melody'); ta.value = ta.value.trim().split(/\s+/).slice(0, -1).join(' '); };
$('#clear').onclick = () => { $('#melody').value = ''; };
$('#octave').oninput = drawPiano;
$('#instrument').onchange = () => $('#instrument').blur();

const typing = () => {
  const a = document.activeElement;
  return a && (a.tagName === 'TEXTAREA' || a.tagName === 'SELECT' || (a.tagName === 'INPUT' && !['range', 'checkbox'].includes(a.type)) || a.closest?.('.CodeMirror'));
};
addEventListener('keydown', e => {
  const mod = e.ctrlKey || e.metaKey;
  if (mod && e.key === 'Enter') { e.preventDefault(); render(); return; }
  if (mod && e.key.toLowerCase() === 's') { e.preventDefault(); save(); return; }
  if (e.key === 'Escape') { stop(); return; }
  if (typing() || mod || e.altKey || e.repeat || state.view !== 'code') return;
  if (e.key === ' ' && recording) { e.preventDefault(); write('r'); return; }
  if (e.key === 'Backspace' && recording) { e.preventDefault(); $('#undo').click(); return; }
  const o = keyOffset(e.key.toLowerCase()); if (o === null) return;
  e.preventDefault(); press((+$('#octave').value + 1) * 12 + o);
});

function wrapMelody(text) {
  const lines = []; let row = [], beats = 0;
  for (const tok of text.trim().split(/\s+/)) {
    row.push(tok); beats += +(tok.split(':')[1] || 0);
    if (beats >= 16) { lines.push(row.join(' ')); row = []; beats = 0; }
  }
  if (row.length) lines.push(row.join(' '));
  return lines.map(l => '    ' + l).join('\n');
}
$('#playMelody').onclick = async () => {
  const text = $('#melody').value.trim();
  if (!text) return status(t('st.melodyEmpty'), 'bad');
  audio(); status(t('st.renderingMelody'));
  const code = `m = mel("""${text}""")\ns = Song(bpm=${+$('#bpm').value}, bars=max(1, -int(-beats_of(m) // 4)), loop=False)\n` +
    `s.melody("${$('#instrument').value}", 0, m, gain=0.3, wet=0.3)\nsong = s.render(1.0, 0.12)`;
  try {
    const r = await api('/api/render', { method: 'POST', body: { name: 'melody', code } });
    const b = await ctx.decodeAudioData(await api(`/api/audio/${r.id}`));
    const s = ctx.createBufferSource(); s.buffer = b; s.connect(master); s.start();
    status(t('st.melodyPlaying'), 'ok');
  } catch (e) { status(e.message, 'bad'); }
};
$('#insert').onclick = () => {
  const text = $('#melody').value.trim(); if (!text || state.kind !== 'code') return;
  ed.insert(`s.melody("${$('#instrument').value}", 0, mel("""\n${wrapMelody(text)}\n"""), gain=0.25, wet=0.35)\n`);
};

// ── Language ────────────────────────────────────────────────────────────────
function refreshLanguage() {
  applyI18n();
  $('#lang').textContent = LANG === 'es' ? 'EN' : 'ES';
  $('#record').textContent = t(recording ? 'kb.recording' : 'kb.record');
  if (state.visual && state.visual.project) state.visual.build();
  drawList(); showAnalysis(lastAnalysis);
}
$('#lang').onclick = () => { setLang(LANG === 'es' ? 'en' : 'es'); refreshLanguage(); };

// ── Start-up ────────────────────────────────────────────────────────────────
(async () => {
  applyI18n(); $('#lang').textContent = LANG === 'es' ? 'EN' : 'ES';
  status(t('st.loading'));
  let info;
  try { info = await api('/api/info'); } catch (e) { return status(t('st.noServer', { msg: e.message }), 'bad'); }
  state.info = info;
  state.visual = new VisualEditor($('#visual'), info, {
    onChange: onVisualChange,
    preview: (instrument, pitch, seconds) => playNote(instrument, pitch, seconds, 0.4),
  });

  for (const i of info.instruments) {
    const o = document.createElement('option'); o.value = o.textContent = i.name; o.title = i.description;
    if (i.name === 'flute') o.selected = true;
    $('#instrument').append(o);
  }
  const chipTargets = { melodic: '#chipsMelodic', drum: '#chipsDrum', fx: '#chipsFx' };
  const snippet = i => i.kind === 'melodic' ? `inst.${i.name}(midi(60), s.beat)` : i.kind === 'fx' ? `inst.${i.name}(s.beat * 4)` : `inst.${i.name}()`;
  for (const i of info.instruments) {
    const b = document.createElement('button'); b.textContent = i.name; b.title = `${i.description}\n${snippet(i)}`;
    b.onclick = () => { if (state.kind === 'code') ed.insert(snippet(i)); };
    $(chipTargets[i.kind]).append(b);
  }
  $('#chordKinds').innerHTML = info.chords.map(c => `<code>${c}</code>`).join(' ');
  drawPiano();

  await loadSongs();
  let draft = null;
  try { draft = JSON.parse(localStorage.getItem(DRAFT_KEY) || 'null'); } catch { }
  if (draft && draft.kind && (draft.project || draft.code)) {  // drafts from older versions have no "kind"
    loadSong({ kind: draft.project ? 'visual' : 'code', project: draft.project, code: draft.code || '', name: draft.name || '',
      current: draft.current, view: draft.view });
    state.dirty = !!draft.dirty;
  } else {
    const first = info.presets[0];
    loadSong({ kind: 'visual', project: first.project, name: `my_${first.id}` });
  }
  if (!songs.mine.length) selectTab('examples');
  status(t('st.start', { n: info.instruments.length, e: songs.examples.length }) + (info.ffmpeg ? '' : ' · ' + t('st.noFfmpeg')), 'ok');
})();
