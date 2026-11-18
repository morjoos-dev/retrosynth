// Interface texts in English and Spanish. t('key', {var}) returns the text in the current
// language; elements with data-i18n / data-i18n-title / data-i18n-placeholder are filled in
// automatically by applyI18n().
'use strict';

const I18N = {
  en: {
    'mode.visual': 'Visual', 'mode.code': 'Code',
    'mode.visual.title': 'Compose with tracks, no code needed', 'mode.code.title': 'Write the song as a Python script',
    'name.placeholder': 'song_name', 'name.title': 'Song name (used to save and export)',
    'render': '▶ Play', 'render.title': 'Render and play (Ctrl+Enter)',
    'stop': '■ Stop', 'loop': '⟳ Loop', 'loop.title': 'Loop playback', 'volume': 'Volume',
    'save': 'Save', 'export': 'Export', 'export.title': 'Write WAV, OGG and MP3 to the output folder',
    'openOutput': 'Open the output folder', 'lang.title': 'Cambiar a español',
    'tabs.mine': 'My songs', 'tabs.examples': 'Examples', 'search': 'Search…', 'new': '+ New song',
    'empty.mine': 'No saved songs yet. Press "+ New song" to start.', 'empty.none': 'Nothing found.',
    'delete.title': 'Delete this song', 'delete.confirm': 'Delete "{name}"?',
    'unsaved': 'You have unsaved changes. Continue anyway?',
    'player': 'Player', 'wave.title': 'Click to jump to that point',
    'an.duration': 'Duration', 'an.loudness': 'Loudness', 'an.peak': 'Peak', 'an.clipping': 'Clipping',
    'an.seam': 'Loop seam', 'an.samples': 'Samples', 'an.none': 'none', 'an.clean': 'clean',
    'an.audible': '×{n} (audible)', 'an.clipped': '{n} samples',
    'kb.title': 'Keyboard', 'kb.keys': 'keys', 'kb.instrument': 'Instrument', 'kb.octave': 'Octave', 'kb.length': 'Length',
    'kb.record': '● Record', 'kb.recording': '● Recording', 'kb.rest': 'Rest', 'kb.clear': 'Clear',
    'kb.playMelody': '▶ Play melody', 'kb.insert': 'Insert into code',
    'kb.placeholder': 'Melody: C5:1 E5:0.5 G5:0.5 r:1 …  (pitch:beats, r = rest)',
    'len.0.25': 'sixteenth (0.25)', 'len.0.5': 'eighth (0.5)', 'len.1': 'quarter (1)', 'len.1.5': 'dotted quarter (1.5)',
    'len.2': 'half (2)', 'len.3': 'dotted half (3)', 'len.4': 'whole (4)',
    'help.title': 'Cheat sheet', 'tips.title': 'How it works',
    'tips.1': '<b>Melody</b>: click the grid to add a note, drag right to make it longer, click a note to delete it.',
    'tips.2': '<b>Chords</b>: pick one chord per bar from the blocks above the melody. They are already in key.',
    'tips.3': '<b>Drums</b>: switch steps on and off. The pattern repeats every bar.',
    'tips.4': '<b>🎲 Surprise me</b> writes a new melody that fits your chords.',
    'tips.5': 'With <b>Live</b> on, every change is heard right away. <b>Code</b> shows the Python behind your song.',
    // status messages
    'st.loading': 'Loading…', 'st.rendering': 'Rendering…', 'st.ready': 'Ready · {d} s of music rendered in {s} s',
    'st.error': 'Error', 'st.opened': 'Opened "{name}"', 'st.saved': 'Saved: {path}', 'st.exporting': 'Exporting…',
    'st.exported': 'Exported {files}', 'st.exportFailed': 'Export failed: {msg}',
    'st.badName': 'Give it a name: letters, digits, _ or -', 'st.noServer': 'Cannot reach the studio server: {msg}',
    'st.start': 'Ready: {n} instruments, {e} examples', 'st.noFfmpeg': 'ffmpeg not found, exports will be WAV only',
    'st.melodyEmpty': 'The melody is empty: record or type some notes', 'st.melodyPlaying': 'Playing the melody',
    'st.renderingMelody': 'Rendering melody…', 'st.line': 'Line {n}: ',
    // visual editor
    'v.style': 'Style', 'v.tempo': 'Tempo', 'v.key': 'Key', 'v.bars': 'Bars', 'v.reverb': 'Echo', 'v.live': 'Live',
    'v.live.title': 'Re-render automatically after every change',
    'v.melody': 'Melody', 'v.chords': 'Chords', 'v.bass': 'Bass', 'v.drums': 'Drums',
    'v.instrument': 'Instrument', 'v.vol': 'Vol', 'v.pan': 'Pan', 'v.noteLen': 'Note', 'v.pattern': 'Pattern',
    'v.surprise': '🎲 Surprise me', 'v.surprise.title': 'Write a new random melody that fits the chords',
    'v.clearMelody': 'Clear', 'v.up': 'Higher notes', 'v.down': 'Lower notes', 'v.addDrum': '+ Add drum…',
    'v.removeRow': 'Remove this drum', 'v.bar': 'Bar {n}', 'v.noChord': '—',
    'v.codeBanner': 'This code is generated from the visual editor and updates by itself.',
    'v.editAsCode': 'Edit as code', 'v.editAsCode.confirm': 'Edit this song as code? From then on it can only be changed in the Code view (the visual editor will not be able to open it).',
    'v.isCode': 'This song is written in code, so it cannot be shown as tracks.',
    'v.newVisual': 'Start a new visual song', 'v.backToCode': 'Back to the code',
    'scale.major': 'major', 'scale.minor': 'minor', 'scale.phrygian_dominant': 'exotic (Phrygian dom.)',
    'cs.pad': 'Sustained', 'cs.arpeggio': 'Arpeggio', 'cs.fast_arpeggio': 'Fast arpeggio', 'cs.stabs': 'Rhythmic', 'cs.off': 'Off',
    'bs.root': 'Long notes', 'bs.root_fifth': 'Root & fifth', 'bs.eighths': 'Driving eighths', 'bs.octaves': 'Octaves', 'bs.off': 'Off',
    'nl.1': '1/16', 'nl.2': '1/8', 'nl.4': '1/4', 'nl.8': '1/2', 'nl.16': 'whole',
    'drum.kick': 'Kick', 'drum.snare': 'Snare', 'drum.hihat': 'Hi-hat', 'drum.open_hat': 'Open hat', 'drum.claps': 'Claps',
    'drum.tom': 'Tom', 'drum.shaker': 'Shaker', 'drum.tambourine': 'Tambourine', 'drum.doum': 'Doumbek (low)',
    'drum.tek': 'Doumbek (high)', 'drum.crash': 'Crash',
    'new.title': 'New song', 'new.subtitle': 'Choose a style to start from. You can change everything afterwards.',
    'new.code': '</> Write code instead', 'new.cancel': 'Cancel', 'new.replace': 'Replace the current song with the "{name}" style?',
  },
  es: {
    'mode.visual': 'Visual', 'mode.code': 'Código',
    'mode.visual.title': 'Compón con pistas, sin escribir código', 'mode.code.title': 'Escribe el tema como un script de Python',
    'name.placeholder': 'nombre_del_tema', 'name.title': 'Nombre del tema (para guardar y exportar)',
    'render': '▶ Escuchar', 'render.title': 'Generar y escuchar (Ctrl+Enter)',
    'stop': '■ Parar', 'loop': '⟳ Bucle', 'loop.title': 'Repetir en bucle', 'volume': 'Volumen',
    'save': 'Guardar', 'export': 'Exportar', 'export.title': 'Guardar WAV, OGG y MP3 en la carpeta de salida',
    'openOutput': 'Abrir la carpeta de salida', 'lang.title': 'Switch to English',
    'tabs.mine': 'Mis temas', 'tabs.examples': 'Ejemplos', 'search': 'Buscar…', 'new': '+ Tema nuevo',
    'empty.mine': 'Aún no has guardado ningún tema. Pulsa «+ Tema nuevo» para empezar.', 'empty.none': 'No hay resultados.',
    'delete.title': 'Borrar este tema', 'delete.confirm': '¿Borrar «{name}»?',
    'unsaved': 'Hay cambios sin guardar. ¿Continuar igualmente?',
    'player': 'Reproductor', 'wave.title': 'Clic para saltar a ese punto',
    'an.duration': 'Duración', 'an.loudness': 'Volumen', 'an.peak': 'Pico', 'an.clipping': 'Saturación',
    'an.seam': 'Empalme del bucle', 'an.samples': 'Muestras', 'an.none': 'ninguna', 'an.clean': 'limpio',
    'an.audible': '×{n} (se notará)', 'an.clipped': '{n} muestras',
    'kb.title': 'Teclado', 'kb.keys': 'teclas', 'kb.instrument': 'Instrumento', 'kb.octave': 'Octava', 'kb.length': 'Duración',
    'kb.record': '● Grabar', 'kb.recording': '● Grabando', 'kb.rest': 'Silencio', 'kb.clear': 'Borrar',
    'kb.playMelody': '▶ Escuchar melodía', 'kb.insert': 'Insertar en el código',
    'kb.placeholder': 'Melodía: C5:1 E5:0.5 G5:0.5 r:1 …  (nota:tiempos, r = silencio)',
    'len.0.25': 'semicorchea (0.25)', 'len.0.5': 'corchea (0.5)', 'len.1': 'negra (1)', 'len.1.5': 'negra con puntillo (1.5)',
    'len.2': 'blanca (2)', 'len.3': 'blanca con puntillo (3)', 'len.4': 'redonda (4)',
    'help.title': 'Chuleta', 'tips.title': 'Cómo funciona',
    'tips.1': '<b>Melodía</b>: haz clic en la cuadrícula para poner una nota, arrastra a la derecha para alargarla y haz clic en una nota para quitarla.',
    'tips.2': '<b>Acordes</b>: elige un acorde por compás en los bloques de encima de la melodía. Ya están en la tonalidad.',
    'tips.3': '<b>Batería</b>: enciende y apaga los pasos. El ritmo se repite en cada compás.',
    'tips.4': '<b>🎲 Sorpréndeme</b> compone una melodía nueva que encaja con tus acordes.',
    'tips.5': 'Con <b>En vivo</b> activado, cada cambio se oye al momento. <b>Código</b> muestra el Python que hay detrás.',
    'st.loading': 'Cargando…', 'st.rendering': 'Generando…', 'st.ready': 'Listo · {d} s de música generados en {s} s',
    'st.error': 'Error', 'st.opened': 'Abierto «{name}»', 'st.saved': 'Guardado: {path}', 'st.exporting': 'Exportando…',
    'st.exported': 'Exportado: {files}', 'st.exportFailed': 'No se pudo exportar: {msg}',
    'st.badName': 'Ponle un nombre: letras sin tilde, números, _ o -', 'st.noServer': 'No se puede conectar con el servidor: {msg}',
    'st.start': 'Listo: {n} instrumentos, {e} ejemplos', 'st.noFfmpeg': 'no se encontró ffmpeg, solo se exportará WAV',
    'st.melodyEmpty': 'La melodía está vacía: graba o escribe notas', 'st.melodyPlaying': 'Sonando la melodía',
    'st.renderingMelody': 'Generando la melodía…', 'st.line': 'Línea {n}: ',
    'v.style': 'Estilo', 'v.tempo': 'Tempo', 'v.key': 'Tono', 'v.bars': 'Compases', 'v.reverb': 'Eco', 'v.live': 'En vivo',
    'v.live.title': 'Volver a generar automáticamente tras cada cambio',
    'v.melody': 'Melodía', 'v.chords': 'Acordes', 'v.bass': 'Bajo', 'v.drums': 'Batería',
    'v.instrument': 'Instrumento', 'v.vol': 'Vol', 'v.pan': 'Pan', 'v.noteLen': 'Nota', 'v.pattern': 'Patrón',
    'v.surprise': '🎲 Sorpréndeme', 'v.surprise.title': 'Compone una melodía nueva al azar que encaja con los acordes',
    'v.clearMelody': 'Borrar', 'v.up': 'Notas más agudas', 'v.down': 'Notas más graves', 'v.addDrum': '+ Añadir tambor…',
    'v.removeRow': 'Quitar este tambor', 'v.bar': 'Compás {n}', 'v.noChord': '—',
    'v.codeBanner': 'Este código se genera a partir del editor visual y se actualiza solo.',
    'v.editAsCode': 'Editar como código', 'v.editAsCode.confirm': '¿Editar este tema como código? A partir de entonces solo se podrá cambiar en la vista Código (el editor visual ya no podrá abrirlo).',
    'v.isCode': 'Este tema está escrito en código, así que no se puede mostrar como pistas.',
    'v.newVisual': 'Empezar un tema visual nuevo', 'v.backToCode': 'Volver al código',
    'scale.major': 'mayor', 'scale.minor': 'menor', 'scale.phrygian_dominant': 'exótica (frigia dom.)',
    'cs.pad': 'Sostenidos', 'cs.arpeggio': 'Arpegio', 'cs.fast_arpeggio': 'Arpegio rápido', 'cs.stabs': 'Rítmicos', 'cs.off': 'Apagado',
    'bs.root': 'Notas largas', 'bs.root_fifth': 'Raíz y quinta', 'bs.eighths': 'Corcheas', 'bs.octaves': 'Octavas', 'bs.off': 'Apagado',
    'nl.1': '1/16', 'nl.2': '1/8', 'nl.4': '1/4', 'nl.8': '1/2', 'nl.16': 'redonda',
    'drum.kick': 'Bombo', 'drum.snare': 'Caja', 'drum.hihat': 'Charles', 'drum.open_hat': 'Charles abierto', 'drum.claps': 'Palmas',
    'drum.tom': 'Tom', 'drum.shaker': 'Maraca', 'drum.tambourine': 'Pandereta', 'drum.doum': 'Darbuka (grave)',
    'drum.tek': 'Darbuka (agudo)', 'drum.crash': 'Platillo',
    'new.title': 'Tema nuevo', 'new.subtitle': 'Elige un estilo para empezar. Después puedes cambiarlo todo.',
    'new.code': '</> Prefiero escribir código', 'new.cancel': 'Cancelar', 'new.replace': '¿Sustituir el tema actual por el estilo «{name}»?',
  },
};

let LANG = (() => {
  try { const saved = localStorage.getItem('retrosynth.lang'); if (saved in I18N) return saved; } catch { }
  return (navigator.language || 'en').toLowerCase().startsWith('es') ? 'es' : 'en';
})();

function t(key, vars = {}) {
  const text = I18N[LANG][key] ?? I18N.en[key] ?? key;
  return text.replace(/\{(\w+)\}/g, (_, k) => (k in vars ? vars[k] : `{${k}}`));
}

function applyI18n(root = document) {
  document.documentElement.lang = LANG;
  root.querySelectorAll('[data-i18n]').forEach(e => { e.textContent = t(e.dataset.i18n); });
  root.querySelectorAll('[data-i18n-html]').forEach(e => { e.innerHTML = t(e.dataset.i18nHtml); });
  root.querySelectorAll('[data-i18n-title]').forEach(e => { e.title = t(e.dataset.i18nTitle); });
  root.querySelectorAll('[data-i18n-label]').forEach(e => { e.setAttribute('aria-label', t(e.dataset.i18nLabel)); });
  root.querySelectorAll('[data-i18n-placeholder]').forEach(e => { e.placeholder = t(e.dataset.i18nPlaceholder); });
}

function setLang(lang) {
  LANG = lang;
  try { localStorage.setItem('retrosynth.lang', lang); } catch { }
  applyI18n();
}
