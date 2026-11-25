// Options / pause menu: sound sliders (PREP-AV 25 Nov; owner 25 Nov 07:5x "follow lol or dota": no hotkey, sliders in the options menu
// opened with Esc). Master, music, effects, voice and ambience (one slider for the voice and ambience buses), mute. Saved by sound.js
// (localStorage inside try/catch). Built once at boot with createElement (no inline styles or handlers); every string is a TEXT key.
// The game owns opening and closing (Esc, the touch menu button), the pause, and the CSS (OPT_CSS, pasted into the one <style> block).

// New TEXT keys and their English text (INT copies these into TEXT; a missing key fails the runtime check).
export const OPT_TEXT = {
  opt_title: 'Options',
  opt_sound: 'Sound',
  opt_master: 'Master volume',
  opt_music: 'Music',
  opt_sfx: 'Effects',
  opt_voice: 'Voice and ambience',
  opt_mute: 'Mute all',
  opt_unmute: 'Sound on',
  opt_resume: 'Resume',
  opt_btn: 'Menu',
  opt_hint: 'Esc returns to the game',
};

// Sliders: TEXT key, the sound.js buses it drives (the first one is read back when the menu opens).
export const OPT_SLIDERS = [
  ['opt_master', ['master']],
  ['opt_music', ['music']],
  ['opt_sfx', ['sfx']],
  ['opt_voice', ['voice', 'amb']],
];

// CSS for the one <style> block (BEM classes, is-hidden state; 44 px targets on every control, also on phones).
export const OPT_CSS = `.opts{position:fixed;inset:0;z-index:10;display:flex;align-items:center;justify-content:center;background:#120d16e6}
.opts.is-hidden{display:none}
.opts__box{width:min(92vw,460px);padding:20px 18px;background:#1b1620;border:2px solid #c9a040;border-radius:10px;color:#f3e6c8;font:15px system-ui,sans-serif}
.opts__title{margin:0 0 4px;font:italic 24px Georgia,serif;color:#ffd98a;text-align:center}
.opts__sub{margin:10px 0 6px;font:bold 13px system-ui,sans-serif;color:#cfc2a8;text-transform:uppercase;letter-spacing:.08em}
.opts__row{display:grid;grid-template-columns:1fr 2fr 3.2em;align-items:center;gap:10px;min-height:44px}
.opts__range{width:100%;min-height:44px;margin:0;accent-color:#c9a040;touch-action:pan-x}
.opts__val{text-align:right;font-variant-numeric:tabular-nums}
.opts__btns{display:flex;gap:10px;justify-content:center;margin-top:14px;flex-wrap:wrap}
.opts__btn{min-width:44px;min-height:44px;padding:10px 18px;font:15px system-ui,sans-serif;color:#fff;background:#2a2030;border:2px solid #6a5a7a;border-radius:8px}
.opts__btn.is-on{background:#5a1a1a;border-color:#f88}
.opts__hint{margin-top:10px;text-align:center;font:12px system-ui,sans-serif;color:#bbb}
.opts-open{position:fixed;right:12px;top:10px;min-width:44px;min-height:44px;z-index:7;font:15px system-ui,sans-serif;background:#3a2a3a;color:#fff;border:1px solid #b99;border-radius:8px;display:none}
body.touch .opts-open{display:block;top:auto;bottom:64px;right:auto;left:10px}
body.touch .opts__hint{display:none}`;

// root = document.body (or any element); T = the game's text function; snd = the sound.js namespace; onResume = the game's close handler.
// Returns { el, openBtn, open(), close(), isOpen(), sync() }.
export function buildOptions(root, T, snd, onResume) {
  const doc = root.ownerDocument || document;
  const mk = (tag, cls, parent) => { const e = doc.createElement(tag); if (cls) e.className = cls; if (parent) parent.appendChild(e); return e; };
  const el = mk('section', 'opts is-hidden', root);
  el.id = 'opts'; el.setAttribute('role', 'dialog'); el.setAttribute('aria-modal', 'true'); el.setAttribute('aria-labelledby', 'optsTitle');
  const box = mk('div', 'opts__box', el);
  const h = mk('h2', 'opts__title', box); h.id = 'optsTitle'; h.textContent = T('opt_title');
  mk('h3', 'opts__sub', box).textContent = T('opt_sound');
  const rows = [];
  for (const [key, buses] of OPT_SLIDERS) {
    const row = mk('label', 'opts__row', box);
    mk('span', 'opts__label', row).textContent = T(key);
    const r = mk('input', 'opts__range', row);
    r.type = 'range'; r.min = '0'; r.max = '100'; r.step = '1'; r.dataset.key = key;
    const out = mk('output', 'opts__val', row);
    const apply = (save) => {
      const v = +r.value / 100;
      for (let i = 0; i < buses.length; i++) snd.setVolume(buses[i], v, !save);
      const txt = r.value + '%';
      if (out.textContent !== txt) out.textContent = txt;
    };
    r.addEventListener('input', () => apply(false));
    r.addEventListener('change', () => apply(true));
    rows.push({ r, out, buses });
  }
  const btns = mk('div', 'opts__btns', box);
  const mute = mk('button', 'opts__btn opts__btn--mute', btns); mute.type = 'button';
  const resume = mk('button', 'opts__btn opts__btn--resume', btns); resume.type = 'button'; resume.textContent = T('opt_resume');
  mk('p', 'opts__hint', box).textContent = T('opt_hint');
  const openBtn = mk('button', 'opts-open', root); openBtn.type = 'button'; openBtn.id = 'btnOpts'; openBtn.textContent = T('opt_btn');
  const showMute = () => {
    const on = !!snd.status().mute;
    mute.classList.toggle('is-on', on); mute.setAttribute('aria-pressed', on ? 'true' : 'false');
    mute.textContent = T(on ? 'opt_unmute' : 'opt_mute');
  };
  mute.addEventListener('click', () => { snd.setMute(!snd.status().mute); showMute(); });
  resume.addEventListener('click', () => { if (onResume) onResume(); });
  let back = null;
  function sync() {
    for (const x of rows) { x.r.value = String(Math.round(snd.getVolume(x.buses[0]) * 100)); x.out.textContent = x.r.value + '%'; }
    showMute();
  }
  function open() {
    if (isOpen()) return;
    back = doc.activeElement; sync(); el.classList.remove('is-hidden'); rows[0].r.focus();
  }
  function close() {
    if (!isOpen()) return;
    el.classList.add('is-hidden'); if (back && back.focus) back.focus(); back = null;
  }
  function isOpen() { return !el.classList.contains('is-hidden'); }
  sync();
  return { el, openBtn, open, close, isOpen, sync };
}
