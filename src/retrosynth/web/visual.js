// Visual editor: compose with tracks (chords, melody piano roll, bass, drum steps) instead of code.
// It edits a "project" object; the server turns projects into song scripts (see arrange.py).
'use strict';

// ── Music theory helpers ─────────────────────────────────────────────────────
const PITCH_CLASS = { C: 0, 'C#': 1, Db: 1, D: 2, 'D#': 3, Eb: 3, E: 4, F: 5, 'F#': 6, Gb: 6, G: 7, 'G#': 8, Ab: 8, A: 9, 'A#': 10, Bb: 10, B: 11 };
const SHARPS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
const FLATS = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B'];
const CHORD_INTERVALS = { '': [0, 4, 7], m: [0, 3, 7], 7: [0, 4, 7, 10], m7: [0, 3, 7, 10], maj7: [0, 4, 7, 11], dim: [0, 3, 6], aug: [0, 4, 8], sus2: [0, 2, 7], sus4: [0, 5, 7], add9: [0, 4, 7, 14] };
const CHORD_RE = /^([A-G][#b]?)(maj7|m7|sus2|sus4|add9|dim|aug|m|7)?$/;
const mod12 = n => ((n % 12) + 12) % 12;

function chordNotes(symbol, octave = 3) {
  const m = CHORD_RE.exec(symbol || '');
  if (!m) return null;
  const root = 12 * (octave + 1) + PITCH_CLASS[m[1]];
  return CHORD_INTERVALS[m[2] || ''].map(i => root + i);
}
function usesFlats(key, scale) {
  return (scale === 'major' ? ['F', 'Bb', 'Eb', 'Ab', 'Db'] : ['D', 'G', 'C', 'F', 'Bb', 'Eb']).includes(key);
}
const pcName = (pc, key, scale) => (usesFlats(key, scale) ? FLATS : SHARPS)[mod12(pc)];
const noteLabel = m => SHARPS[mod12(m)] + (Math.floor(m / 12) - 1);

/** Chords that belong to the key (triads on every degree, plus the usual dominant sevenths). */
function chordPalette(key, scale, scales) {
  const root = PITCH_CLASS[key], steps = scales[scale], out = [];
  for (let d = 0; d < 7; d++) {
    const at = k => steps[(d + k) % 7] + ((d + k) >= 7 ? 12 : 0);
    const third = at(2) - at(0), fifth = at(4) - at(0);
    const suffix = third === 4 && fifth === 7 ? '' : third === 3 && fifth === 7 ? 'm' : third === 3 && fifth === 6 ? 'dim' : third === 4 && fifth === 8 ? 'aug' : null;
    if (suffix !== null) out.push(pcName(root + steps[d], key, scale) + suffix);
  }
  const five = pcName(root + 7, key, scale);
  if (scale === 'major') out.push(five + '7');
  if (scale === 'minor') out.push(five, five + '7');  // harmonic-minor dominant
  return [...new Set(out)];
}
const scalePitchClasses = (key, scale, scales) => new Set(scales[scale].map(s => mod12(PITCH_CLASS[key] + s)));
function transposeChord(symbol, delta, key, scale) {
  const m = CHORD_RE.exec(symbol || '');
  return m ? pcName(PITCH_CLASS[m[1]] + delta, key, scale) + (m[2] || '') : symbol;
}

/** A new melody that fits the chords: chord tones on strong beats, mostly stepwise motion. */
function surpriseMelody(p, scales) {
  const pcs = scalePitchClasses(p.key, p.scale, scales);
  const pool = []; for (let m = 67; m <= 86; m++) if (pcs.has(mod12(m))) pool.push(m);
  const rhythms = [[4, 4, 4, 4], [4, 2, 2, 4, 4], [6, 2, 4, 4], [2, 2, 2, 2, 4, 4], [8, 4, 4], [4, 4, 8], [2, 2, 4, 2, 2, 4], [6, 2, 8], [4, 4, 4, 2, 2], [3, 1, 4, 4, 4]];
  const pickWeighted = (items, weight) => {
    const w = items.map(weight), total = w.reduce((a, b) => a + b, 0);
    let r = Math.random() * total;
    for (let i = 0; i < items.length; i++) { r -= w[i]; if (r <= 0) return items[i]; }
    return items[items.length - 1];
  };
  const notes = []; let prev = pool[Math.floor(pool.length / 2)], motif = null;
  for (let bar = 0; bar < p.bars; bar++) {
    const chord = chordNotes(p.tracks.chords.chords[bar]);
    const chordPcs = chord ? chord.map(mod12) : [mod12(PITCH_CLASS[p.key])];
    const last = bar === p.bars - 1;
    let rhythm = last ? [4, 4, 8] : (bar % 2 === 1 && motif && Math.random() < 0.6) ? motif : rhythms[Math.floor(Math.random() * rhythms.length)];
    if (bar % 2 === 0) motif = rhythm;
    let step = bar * 16;
    rhythm.forEach((len, i) => {
      const final = last && i === rhythm.length - 1;
      if (!final && i > 0 && Math.random() < 0.07) { step += len; return; }  // an occasional rest
      const strong = step % 8 === 0 || final;
      let candidates = pool.filter(m => Math.abs(m - prev) <= (strong ? 7 : 4));
      if (strong || final) candidates = candidates.filter(m => chordPcs.includes(mod12(m)));
      if (final) candidates = candidates.filter(m => mod12(m) === chordPcs[0]);
      if (!candidates.length) candidates = pool.filter(m => chordPcs.includes(mod12(m)));
      const pitch = pickWeighted(candidates, m => (m === prev ? 0.4 : 1) / (1 + Math.abs(m - prev)));
      notes.push({ pitch, start: step, length: len });
      prev = pitch; step += len;
    });
  }
  return notes;
}

// ── Editor ──────────────────────────────────────────────────────────────────
const CELL = 14, ROW = 13, ROWS = 25, KEYS_W = 46;
const el = (tag, attrs = {}, ...children) => {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === 'class') e.className = v; else if (k === 'text') e.textContent = v;
    else if (k.startsWith('on')) e[k] = v; else if (v !== undefined && v !== null) e.setAttribute(k, v);
  }
  for (const c of children) if (c) e.append(c);
  return e;
};
const options = (select, items, value) => {
  select.innerHTML = '';
  for (const [v, label] of items) select.append(el('option', { value: v, text: label }));
  select.value = value;
  return select;
};

class VisualEditor {
  /**
   * @param root      container element
   * @param info      /api/info response (instruments, visual options, presets)
   * @param hooks     { onChange(project, {live}), preview(instrument, pitch, seconds) }
   */
  constructor(root, info, hooks) {
    this.root = root; this.info = info; this.hooks = hooks;
    this.scales = info.visual.scales;
    this.melodic = info.instruments.filter(i => i.kind === 'melodic').map(i => i.name);
    this.noteLength = 4; this.low = 72; this.live = true;
    this.project = null;
  }

  load(project) {
    this.project = JSON.parse(JSON.stringify(project));
    const pitches = this.project.tracks.melody.notes.map(n => n.pitch);
    if (pitches.length) {
      const lo = Math.min(...pitches), hi = Math.max(...pitches);
      this.low = Math.max(24, Math.min(Math.floor(lo / 12) * 12, hi - ROWS + 1));
    }
    this.build();
  }

  get steps() { return this.project.bars * 16; }

  changed(structural = false) {
    if (structural) this.build(); else this.drawRoll();
    this.hooks.onChange(this.project);
  }

  // ── Layout ─────────────────────────────────────────────────────────────────
  build() {
    const p = this.project, tr = p.tracks;
    this.root.innerHTML = '';

    // global controls
    const preset = options(el('select', { 'aria-label': t('v.style') }),
      [['', '—'], ...this.info.presets.map(x => [x.id, `${x.icon} ${x.name[LANG] || x.name.en}`])], '');
    preset.onchange = () => {
      const chosen = this.info.presets.find(x => x.id === preset.value);
      if (chosen && confirm(t('new.replace', { name: chosen.name[LANG] || chosen.name.en }))) { this.load(chosen.project); this.hooks.onChange(this.project); }
      else preset.value = '';
    };
    const tempoOut = el('output', { text: p.bpm });
    const tempo = el('input', { type: 'range', min: 40, max: 240, value: p.bpm, 'aria-label': t('v.tempo') });
    tempo.oninput = () => { tempoOut.textContent = tempo.value; };
    tempo.onchange = () => { p.bpm = +tempo.value; this.changed(); };
    const key = options(el('select', { 'aria-label': t('v.key') }), this.info.visual.keys.map(k => [k, k]), p.key);
    key.onchange = () => this.setKey(key.value);
    const scale = options(el('select', { 'aria-label': t('v.key') }), Object.keys(this.scales).map(s => [s, t('scale.' + s)]), p.scale);
    scale.onchange = () => { p.scale = scale.value; this.changed(true); };
    const bars = options(el('select', { 'aria-label': t('v.bars') }), [4, 8, 12, 16].map(n => [n, n]), p.bars);
    bars.onchange = () => this.setBars(+bars.value);
    const reverb = el('input', { type: 'range', min: 0.3, max: 2.5, step: 0.1, value: p.reverb, 'aria-label': t('v.reverb') });
    reverb.onchange = () => { p.reverb = +reverb.value; this.changed(); };
    const live = el('input', { type: 'checkbox', id: 'vLive' }); live.checked = this.live;
    live.onchange = () => { this.live = live.checked; };
    this.root.append(el('div', { class: 'v-top' },
      el('label', {}, t('v.style'), preset),
      el('label', {}, t('v.tempo'), tempo, tempoOut),
      el('label', {}, t('v.key'), key, scale),
      el('label', {}, t('v.bars'), bars),
      el('label', {}, t('v.reverb'), reverb),
      el('label', { title: t('v.live.title'), class: 'v-live' }, live, t('v.live')),
    ));

    // chords + melody share one horizontally scrolling timeline
    const chordStyle = options(el('select'), this.info.visual.chord_styles.map(s => [s, t('cs.' + s)]), tr.chords.style);
    chordStyle.onchange = () => { tr.chords.style = chordStyle.value; this.changed(); };
    const noteLen = options(el('select', { 'aria-label': t('v.noteLen') }), [1, 2, 4, 8, 16].map(n => [n, t('nl.' + n)]), this.noteLength);
    noteLen.onchange = () => { this.noteLength = +noteLen.value; };
    this.upBtn = el('button', { class: 'icon', title: t('v.up'), 'aria-label': t('v.up'), onclick: () => this.shift(12) });
    this.downBtn = el('button', { class: 'icon', title: t('v.down'), 'aria-label': t('v.down'), onclick: () => this.shift(-12) });
    this.root.append(
      this.trackHeader('🎹', t('v.chords'), tr.chords, [el('label', {}, t('v.pattern'), chordStyle)]),
      this.trackHeader('🎵', t('v.melody'), tr.melody, [
        this.slider(t('v.pan'), -1, 1, 0.1, tr.melody, 'pan'),
        el('label', {}, t('v.noteLen'), noteLen),
        el('button', { text: t('v.surprise'), title: t('v.surprise.title'), class: 'accent', onclick: () => {
          tr.melody.notes = surpriseMelody(p, this.scales); this.fitView(); this.changed();
        } }),
        el('button', { text: t('v.clearMelody'), onclick: () => { tr.melody.notes = []; this.changed(); } }),
        this.downBtn, this.upBtn,
      ]),
    );

    const scroll = el('div', { class: 'v-scroll' });
    const grid = el('div', { class: 'v-grid' });
    grid.style.gridTemplateColumns = `${KEYS_W}px ${this.steps * CELL}px`;
    // ruler
    const ruler = el('div', { class: 'v-ruler' });
    for (let b = 0; b < p.bars; b++) ruler.append(el('span', { text: b + 1, style: `width:${16 * CELL}px` }));
    // chord lane
    const palette = chordPalette(p.key, p.scale, this.scales);
    const lane = el('div', { class: 'v-chords' });
    tr.chords.chords.forEach((sym, b) => {
      const list = [['', t('v.noChord')], ...palette.map(c => [c, c])];
      if (sym && !palette.includes(sym)) list.push([sym, sym]);
      const s = options(el('select', { 'aria-label': t('v.bar', { n: b + 1 }), style: `width:${16 * CELL - 4}px` }), list, sym);
      s.classList.toggle('empty', !sym);
      s.onchange = () => {
        tr.chords.chords[b] = s.value; s.classList.toggle('empty', !s.value);
        const notes = chordNotes(s.value);
        if (notes) notes.forEach(n => this.hooks.preview(tr.chords.instrument, n + 12, 0.8));
        this.changed();
      };
      lane.append(s);
    });
    // piano keys + roll
    this.keys = el('div', { class: 'v-keys' });
    this.canvas = el('canvas', { class: 'v-roll', 'aria-label': t('v.melody') });
    this.playhead = el('div', { class: 'v-playhead', hidden: '' });
    const rollBox = el('div', { class: 'v-rollbox' }, this.canvas, this.playhead);
    grid.append(el('div', { class: 'v-corner' }), ruler, el('div', { class: 'v-corner' }), lane, this.keys, rollBox);
    scroll.append(grid);
    this.root.append(scroll);
    this.setupRoll();

    // bass
    const bassStyle = options(el('select'), this.info.visual.bass_styles.map(s => [s, t('bs.' + s)]), tr.bass.style);
    bassStyle.onchange = () => { tr.bass.style = bassStyle.value; this.changed(); };
    this.root.append(this.trackHeader('🎸', t('v.bass'), tr.bass, [el('label', {}, t('v.pattern'), bassStyle)]));

    // drums
    const present = Object.keys(tr.drums.rows);
    const add = options(el('select', { 'aria-label': t('v.addDrum') }),
      [['', t('v.addDrum')], ...this.info.visual.drum_rows.filter(r => !present.includes(r.id)).map(r => [r.id, t('drum.' + r.id)])], '');
    add.onchange = () => { if (add.value) { tr.drums.rows[add.value] = '.'.repeat(16); this.changed(true); } };
    this.root.append(this.trackHeader('🥁', t('v.drums'), tr.drums, [add], false));
    const drums = el('div', { class: 'v-drums' });
    this.drumCells = [];
    for (const row of present) {
      const cells = el('div', { class: 'v-steps' });
      [...tr.drums.rows[row]].forEach((ch, i) => {
        const b = el('button', { class: 'step' + (ch === 'x' ? ' on' : ch === 'X' ? ' on accent' : '') + (i % 4 === 0 ? ' beat' : ''),
          'aria-label': `${t('drum.' + row)} ${i + 1}`, 'aria-pressed': ch !== '.' });
        b.onclick = e => {
          const cur = tr.drums.rows[row][i], next = cur !== '.' ? '.' : e.shiftKey ? 'X' : 'x';
          tr.drums.rows[row] = tr.drums.rows[row].slice(0, i) + next + tr.drums.rows[row].slice(i + 1);
          b.className = 'step' + (next === 'x' ? ' on' : next === 'X' ? ' on accent' : '') + (i % 4 === 0 ? ' beat' : '');
          b.setAttribute('aria-pressed', next !== '.');
          if (next !== '.') this.hooks.preview(this.info.visual.drum_rows.find(r => r.id === row).instrument, 60, 0.3);
          this.changed();
        };
        cells.append(b); (this.drumCells[i] ||= []).push(b);
      });
      drums.append(el('div', { class: 'v-drumrow' },
        el('span', { class: 'v-drumname', text: t('drum.' + row) }),
        el('button', { class: 'icon x', text: '✕', title: t('v.removeRow'), 'aria-label': t('v.removeRow'),
          onclick: () => { delete tr.drums.rows[row]; this.changed(true); } }),
        cells));
    }
    this.root.append(drums);
    this.drawRoll();
  }

  trackHeader(icon, title, track, extra, withInstrument = true) {
    const items = [el('h3', {}, el('span', { class: 'v-icon', text: icon, 'aria-hidden': 'true' }), title)];
    if (withInstrument) {
      const s = options(el('select', { 'aria-label': `${title}: ${t('v.instrument')}` }), this.melodic.map(n => [n, n]), track.instrument);
      s.onchange = () => { track.instrument = s.value; this.hooks.preview(s.value, 72, 0.5); this.changed(); };
      items.push(s);
    }
    items.push(this.slider(t('v.vol'), 0, 1.5, 0.05, track, 'volume'), ...extra);
    return el('div', { class: 'v-track' }, ...items);
  }

  slider(label, min, max, step, obj, prop) {
    const input = el('input', { type: 'range', min, max, step, value: obj[prop], 'aria-label': label });
    input.onchange = () => { obj[prop] = +input.value; this.changed(); };
    return el('label', {}, label, input);
  }

  // ── Global edits ───────────────────────────────────────────────────────────
  setKey(newKey) {
    const p = this.project, delta = mod12(PITCH_CLASS[newKey] - PITCH_CLASS[p.key]), shift = delta > 6 ? delta - 12 : delta;
    p.key = newKey;
    p.tracks.melody.notes.forEach(n => { n.pitch += shift; });
    p.tracks.chords.chords = p.tracks.chords.chords.map(c => transposeChord(c, shift, p.key, p.scale));
    this.changed(true);
  }

  setBars(n) {
    const p = this.project, old = p.tracks.chords.chords;
    p.tracks.chords.chords = Array.from({ length: n }, (_, i) => old[i % old.length] ?? '');
    p.bars = n;
    p.tracks.melody.notes = p.tracks.melody.notes.filter(x => x.start < n * 16);
    this.changed(true);
  }

  shift(semitones) { this.low = Math.max(24, Math.min(108 - ROWS + 1, this.low + semitones)); this.drawRoll(); }

  fitView() {
    const pitches = this.project.tracks.melody.notes.map(n => n.pitch);
    if (pitches.length && (Math.min(...pitches) < this.low || Math.max(...pitches) > this.low + ROWS - 1)) {
      this.low = Math.max(24, Math.min(Math.floor(Math.min(...pitches) / 12) * 12, Math.max(...pitches) - ROWS + 1));
    }
  }

  // ── Piano roll ─────────────────────────────────────────────────────────────
  setupRoll() {
    const c = this.canvas;
    let drag = null;
    const cellAt = e => {
      const r = c.getBoundingClientRect();
      return { col: Math.floor((e.clientX - r.left) / CELL), pitch: this.low + ROWS - 1 - Math.floor((e.clientY - r.top) / ROW) };
    };
    c.onpointerdown = e => {
      e.preventDefault();
      const { col, pitch } = cellAt(e), notes = this.project.tracks.melody.notes;
      if (col < 0 || col >= this.steps) return;
      const hit = notes.findIndex(n => n.pitch === pitch && col >= n.start && col < n.start + n.length);
      if (hit >= 0) { notes.splice(hit, 1); this.changed(); return; }
      if (e.button !== 0) return;
      const note = { pitch, start: col, length: Math.min(this.noteLength, this.steps - col) };
      notes.push(note);
      drag = { note, col };
      c.setPointerCapture(e.pointerId);
      this.hooks.preview(this.project.tracks.melody.instrument, pitch, 0.35);
      this.drawRoll();
    };
    c.onpointermove = e => {
      if (!drag) return;
      const { col } = cellAt(e);
      if (col > drag.col) { drag.note.length = Math.min(col, this.steps - 1) - drag.note.start + 1; this.drawRoll(); }
    };
    c.onpointerup = c.onpointercancel = () => {
      if (!drag) return;
      drag = null;
      this.project.tracks.melody.notes.sort((a, b) => a.start - b.start || a.pitch - b.pitch);
      this.changed();
    };
    c.oncontextmenu = e => e.preventDefault();
  }

  drawRoll() {
    if (!this.canvas) return;
    const p = this.project, w = this.steps * CELL, h = ROWS * ROW, dpr = devicePixelRatio || 1;
    const scale = scalePitchClasses(p.key, p.scale, this.scales), tonic = PITCH_CLASS[p.key];
    const c = this.canvas, g = c.getContext('2d');
    c.width = w * dpr; c.height = h * dpr; c.style.width = w + 'px'; c.style.height = h + 'px';
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    const css = getComputedStyle(document.documentElement), v = name => css.getPropertyValue(name).trim();
    // rows: notes of the scale lighter, the tonic highlighted
    for (let r = 0; r < ROWS; r++) {
      const m = this.low + ROWS - 1 - r, pc = mod12(m);
      g.fillStyle = pc === tonic ? v('--roll-tonic') : scale.has(pc) ? v('--roll-in') : v('--roll-out');
      g.fillRect(0, r * ROW, w, ROW);
    }
    // vertical lines: steps, beats, bars
    for (let s = 0; s <= this.steps; s++) {
      g.fillStyle = s % 16 === 0 ? v('--roll-bar') : s % 4 === 0 ? v('--roll-beat') : v('--roll-step');
      g.fillRect(s * CELL, 0, s % 16 === 0 ? 2 : 1, h);
    }
    // notes
    let above = 0, below = 0;
    for (const n of p.tracks.melody.notes) {
      const r = this.low + ROWS - 1 - n.pitch;
      if (r < 0) { above++; continue; }
      if (r >= ROWS) { below++; continue; }
      g.fillStyle = v('--gold'); g.strokeStyle = v('--note-edge'); g.lineWidth = 1;
      g.beginPath(); g.roundRect(n.start * CELL + 1, r * ROW + 1, n.length * CELL - 2, ROW - 2, 3); g.fill(); g.stroke();
    }
    // key labels and out-of-view counts
    this.keys.innerHTML = '';
    for (let r = 0; r < ROWS; r++) {
      const m = this.low + ROWS - 1 - r, black = [1, 3, 6, 8, 10].includes(mod12(m));
      const k = el('div', { class: 'v-key' + (black ? ' black' : ''), text: mod12(m) === 0 || mod12(m) === tonic ? noteLabel(m) : '', style: `height:${ROW}px` });
      k.onpointerdown = () => this.hooks.preview(p.tracks.melody.instrument, m, 0.35);
      this.keys.append(k);
    }
    this.upBtn.textContent = above ? `▲ ${above}` : '▲';
    this.downBtn.textContent = below ? `▼ ${below}` : '▼';
  }

  /** Show where playback is (seconds), or hide the playhead with null. */
  setPlayhead(seconds) {
    if (!this.playhead) return;
    const hide = seconds === null || seconds === undefined;
    this.playhead.hidden = hide;
    const step = hide ? -1 : seconds / (60 / this.project.bpm) * 4;
    if (!hide) this.playhead.style.transform = `translateX(${step * CELL}px)`;
    const col = hide ? -1 : Math.floor(step) % 16;
    if (col !== this.lastCol) {
      (this.drumCells[this.lastCol] || []).forEach(b => b.classList.remove('now'));
      (this.drumCells[col] || []).forEach(b => b.classList.add('now'));
      this.lastCol = col;
    }
  }
}
