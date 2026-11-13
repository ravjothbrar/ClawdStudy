import './styles.css';
import { store, todayCount, streakDays, type Mode } from './store';
import { timer, fmt, durationOf } from './timer/timer';
import { fm } from './music/youtube';
import { chimeBuild, chimeBreak, primeAudio, blip } from './sound';
import type { World, RegionMeta } from './world/world';

const DEBUG = new URLSearchParams(location.search).has('debug');
const TOTAL = 30;

// --------------------------------------------------------------- markup
const CLAWD_SVG = `<svg viewBox="0 0 16 11" class="px" aria-hidden="true"><path fill="currentColor" d="M2 0h12v4h2v2h-2v3H2V6H0V4h2z"/><path fill="#141413" d="M4 2h1v2H4zM11 2h1v2h-1z"/><path fill="currentColor" d="M3 9h1v2H3zM5 9h1v2H5zM10 9h1v2h-1zM12 9h1v2h-1z"/></svg>`;

const app = document.getElementById('app')!;
app.innerHTML = `
<header class="brand">
  <span class="logo">${CLAWD_SVG}</span>
  <div>
    <div class="name">ClawdStudy</div>
    <div class="tag">unofficial fan project · study with Claude FM</div>
  </div>
</header>

<section class="world-card panel" aria-label="World progress">
  <div class="eyebrow"><span>World</span><span id="chapter">Start</span></div>
  <div class="world-count"><span id="count">0</span><span class="of">/ ${TOTAL}</span></div>
  <div class="dots" id="dots" aria-hidden="true"></div>
  <div class="next" id="next"></div>
  <div class="cam-buttons">
    <button class="chip" id="btn-clawd" title="Find Clawd (C)">find clawd</button>
    <button class="chip" id="btn-overview" title="Overview (O)">overview</button>
    <button class="chip" id="btn-album" title="Postcards (P)">album</button>
    <button class="chip icon" id="btn-settings" title="Settings" aria-label="Settings">⚙</button>
  </div>
</section>

<section class="timer panel" aria-label="Pomodoro timer">
  <div class="tabs" role="tablist">
    <button role="tab" data-mode="focus">focus</button>
    <button role="tab" data-mode="short">short break</button>
    <button role="tab" data-mode="long">long break</button>
  </div>
  <div class="eyebrow"><span id="mode-label">Focus</span><span id="cycle"></span></div>
  <div class="time" id="time" aria-live="off">25:00</div>
  <div class="bar"><div id="bar-fill"></div></div>
  <div class="controls">
    <button class="primary" id="btn-start">start</button>
    <button class="ghost" id="btn-reset" title="Give up on this block (nothing gets built)">reset</button>
    <button class="ghost" id="btn-skip" title="Skip">skip</button>
  </div>
  <p class="caption" id="caption"></p>
  <details class="tasks" id="tasks">
    <summary><span>Tasks</span><span id="task-count"></span></summary>
    <ul id="task-list"></ul>
    <form id="task-form" autocomplete="off">
      <input id="task-input" placeholder="What are you working on?" maxlength="120" />
      <input id="task-est" type="number" min="1" max="12" value="1" title="Estimated pomodoros" aria-label="Estimated pomodoros" />
      <button class="chip" type="submit">add</button>
    </form>
  </details>
</section>

<section class="radio panel" aria-label="Claude FM">
  <div class="video" id="video"></div>
  <button class="play" id="btn-play" aria-label="Play Claude FM">
    <svg viewBox="0 0 10 10" aria-hidden="true"><path id="play-icon" fill="currentColor" d="M2 1l7 4-7 4z"/></svg>
  </button>
  <div class="eq" id="eq" aria-hidden="true"><i></i><i></i><i></i><i></i></div>
  <div class="radio-text">
    <div class="station">Claude FM <span class="live">live</span></div>
    <div class="title" id="fm-title">Lo-fi beats to build with</div>
  </div>
  <input type="range" id="vol" min="0" max="100" aria-label="Volume" />
  <button class="chip icon" id="btn-video" title="Show video" aria-label="Toggle video">▢</button>
</section>

<div class="toast" id="toast" role="status" aria-live="polite"></div>

<dialog id="settings" class="panel">
  <form method="dialog">
    <h2>Settings</h2>
    <div class="grid">
      <label>Focus <input type="number" name="focusMin" min="1" max="180" /> min</label>
      <label>Short break <input type="number" name="shortMin" min="1" max="60" /> min</label>
      <label>Long break <input type="number" name="longMin" min="1" max="90" /> min</label>
      <label>Long break every <input type="number" name="longEvery" min="2" max="12" /> blocks</label>
    </div>
    <label class="check"><input type="checkbox" name="autoBreaks" /> Auto-start breaks</label>
    <label class="check"><input type="checkbox" name="autoFocus" /> Auto-start focus after a break</label>
    <label class="check"><input type="checkbox" name="musicOnFocus" /> Play Claude FM when focus starts</label>
    <label class="check"><input type="checkbox" name="sound" /> Chimes</label>
    <label class="check"><input type="checkbox" name="notify" /> Desktop notifications</label>
    <label class="check"><input type="checkbox" name="lowPower" /> Low-power mode (30 fps, no shadows)</label>
    <div class="row">
      <button type="button" class="chip" id="btn-export">export progress</button>
      <label class="chip file">import<input type="file" id="file-import" accept="application/json" hidden /></label>
      <button type="button" class="chip danger" id="btn-wipe">reset world</button>
    </div>
    <p class="fine">Everything is saved in this browser only. ClawdStudy is an unofficial fan project and isn't affiliated with Anthropic. Claude FM is streamed from YouTube.</p>
    <div class="row end"><button class="primary" value="close">done</button></div>
  </form>
</dialog>

<dialog id="album" class="panel wide">
  <form method="dialog">
    <div class="eyebrow"><span>Postcards</span><span id="album-count"></span></div>
    <h2>Every place you've built, path-traced in Blender.</h2>
    <div class="album-grid" id="album-grid"></div>
    <div class="row end"><button class="primary" value="close">close</button></div>
  </form>
</dialog>

<dialog id="photo" class="photo">
  <form method="dialog">
    <img id="photo-img" alt="" />
    <div class="photo-cap"><span id="photo-title"></span><button class="chip" value="close">close</button></div>
  </form>
</dialog>

<dialog id="intro" class="panel">
  <form method="dialog">
    <img class="hero" src="postcards/hero.jpg" alt="Clawd's Archipelago, fully built" onerror="this.remove()" />
    <div class="eyebrow"><span>Welcome</span><span>${CLAWD_SVG}</span></div>
    <h2>Every focus block builds the world.</h2>
    <p>Finish a pomodoro and a new piece of <b>Clawd's Archipelago</b> is built: a café, a lighthouse, a mountain, eventually the moon. Give up halfway and nothing gets built.</p>
    <p>There are <b>${TOTAL}</b> places to unlock. Put on Claude FM and start the timer.</p>
    <p class="fine">Space starts and pauses · drag to look around · scroll to zoom</p>
    <div class="row end"><button class="primary" value="close">let's go</button></div>
  </form>
</dialog>

${DEBUG ? `<div class="debug panel"><b>debug</b>
  <label>unlocked <input type="range" id="dbg-range" min="0" max="${TOTAL}" /></label>
  <button class="chip" id="dbg-complete">complete focus</button>
  <span id="dbg-stats"></span></div>` : ''}
`;

const $ = <T extends HTMLElement = HTMLElement>(id: string) => document.getElementById(id) as T;

// --------------------------------------------------------------- world
let world: World | null = null;
let manifest: RegionMeta[] = [];
const canvas = $('world') as unknown as HTMLCanvasElement;

const unlockedCount = () => Math.min(store.state.completed, TOTAL);

async function bootWorld() {
  const { World } = await import('./world/world');
  world = new World(canvas);
  world.onReady = () => document.body.classList.add('ready');
  world.setLowPower(store.state.settings.lowPower);
  await world.init(unlockedCount());
  manifest = Array.from({ length: world.maxRegion + 1 }, (_, i) => world!.meta(i));
  renderWorldCard();
  world.setMood(timer.running ? (timer.mode === 'focus' ? 'focus' : 'break') : 'idle');
  (window as unknown as { __clawd: unknown }).__clawd = { world, store, timer };
}

// --------------------------------------------------------------- timer UI
const MODE_LABEL: Record<Mode, string> = { focus: 'Focus', short: 'Short break', long: 'Long break' };
const CAPTIONS: Record<Mode, string[]> = {
  focus: [
    'One beat to think, then go.',
    'Phone face down. Clawd is watching.',
    'Sketch the problem first, then fix it.',
    'Deep work mode. Clawd is reading too.',
  ],
  short: ['Stretch, sip some water. Clawd is dancing.', 'Short break. Look at something far away.'],
  long: ['Long break. You earned this one.', 'Walk around. The world will still be here.'],
};

function renderTimer(remaining: number, total: number) {
  const mode = timer.mode;
  $('time').textContent = fmt(remaining);
  $('bar-fill').style.transform = `scaleX(${1 - remaining / total})`;
  $('btn-start').textContent = timer.running ? 'pause' : remaining < total ? 'resume' : 'start';
  $('mode-label').textContent = MODE_LABEL[mode];
  document.querySelectorAll<HTMLButtonElement>('.tabs button').forEach((b) => {
    b.setAttribute('aria-selected', String(b.dataset.mode === mode));
  });
  document.body.dataset.mode = mode;
  document.body.classList.toggle('running', timer.running);
  const s = store.state;
  const inCycle = s.timer.cycle % s.settings.longEvery;
  $('cycle').innerHTML = Array.from(
    { length: s.settings.longEvery },
    (_, i) => `<i class="${i < inCycle || (inCycle === 0 && s.timer.cycle > 0 && mode === 'long') ? 'on' : ''}"></i>`,
  ).join('');
  document.title = timer.running ? `${fmt(remaining)} · ${MODE_LABEL[mode]} · ClawdStudy` : 'ClawdStudy';
}

function setCaption(mode: Mode) {
  const list = CAPTIONS[mode];
  $('caption').textContent = list[Math.floor(Math.random() * list.length)];
}

timer.on((e) => {
  if (e.type === 'tick') renderTimer(e.remaining, e.total);
  if (e.type === 'start') {
    setCaption(e.mode);
    world?.setMood(e.mode === 'focus' ? 'focus' : 'break');
    if (e.mode === 'focus' && store.state.settings.musicOnFocus && fm.state !== 'playing') void fm.play($('video'));
    if (e.mode === 'focus') world?.prefetch(unlockedCount() + 1);
  }
  if (e.type === 'pause') world?.setMood('idle');
  if (e.type === 'mode') setCaption(e.mode);
  if (e.type === 'abandon' && e.mode === 'focus') {
    world?.setMood('idle');
    toast('Nothing built this time', 'Focus blocks only count when you finish them. Clawd believes in you.');
  }
  if (e.type === 'complete') onComplete(e.mode, e.minutes);
});

function onComplete(mode: Mode, minutes: number) {
  const s = store.state.settings;
  if (mode === 'focus') {
    const before = unlockedCount();
    store.update((st) => {
      st.completed += 1;
      const task = st.tasks.find((t) => t.id === st.activeTask);
      if (task) task.act += 1;
      st.history.push({ t: Date.now(), min: minutes, region: st.completed <= TOTAL ? st.completed : null });
    });
    const after = unlockedCount();
    if (s.sound) chimeBuild();
    renderTasks();
    if (after > before && world) {
      const m = world.meta(after);
      notify(`Built: ${m.title}`, m.blurb);
      toast(`New in ${m.chapter} · ${after}/${TOTAL}`, `<b>${m.title}</b><br>${m.blurb}`, 9000, postcard(after));
      world.setMood('break');
      void world.reveal(after).then(renderWorldCard);
    } else {
      notify('Focus block done', 'Take a break. Clawd is dancing.');
      toast('Focus block done', after >= TOTAL ? 'The whole archipelago is built. Clawd is very proud.' : '');
      world?.setMood('break');
    }
    renderWorldCard();
  } else {
    if (s.sound) chimeBreak();
    notify('Break over', 'Ready for another focus block?');
    world?.setMood('idle');
  }
}

function notify(title: string, body: string) {
  if (!store.state.settings.notify || !('Notification' in window) || Notification.permission !== 'granted') return;
  if (!document.hidden) return;
  try {
    new Notification(title, { body, icon: 'favicon.svg', silent: true });
  } catch {
    /* some browsers only allow notifications from a service worker */
  }
}

// --------------------------------------------------------------- world card
function renderWorldCard() {
  const n = unlockedCount();
  $('count').textContent = String(n);
  const cur = manifest[n];
  const next = manifest[n + 1];
  $('chapter').textContent = cur ? cur.chapter : '';
  // dots: one per region in the current chapter, like the effort-level depth dots
  if (manifest.length) {
    const chapter = (next ?? cur).chapter;
    const inChapter = manifest.filter((m) => m.chapter === chapter);
    $('dots').innerHTML = inChapter.map((m) => `<i class="${m.id <= n ? 'on' : ''}" title="${m.title}"></i>`).join('');
  }
  $('next').innerHTML = next
    ? `<span class="k">next build</span> ${next.title}`
    : `<span class="k">complete</span> Every island is built.`;
  const done = todayCount(store.state);
  const streak = streakDays(store.state);
  $('task-count').textContent = `${done} today${streak > 1 ? ` · ${streak} day streak` : ''}`;
  if (DEBUG) ($('dbg-range') as HTMLInputElement).value = String(n);
}

// --------------------------------------------------------------- tasks
function renderTasks() {
  const s = store.state;
  $('task-list').innerHTML = s.tasks
    .map(
      (t) => `<li class="${t.done ? 'done' : ''} ${t.id === s.activeTask ? 'active' : ''}" data-id="${t.id}">
        <button class="tick" data-act="done" aria-label="Toggle done">${t.done ? '✓' : ''}</button>
        <span class="text" data-act="select">${escapeHtml(t.text)}</span>
        <span class="est">${t.act}/${t.est}</span>
        <button class="x" data-act="del" aria-label="Delete task">×</button></li>`,
    )
    .join('');
}

$('task-form').addEventListener('submit', (e) => {
  e.preventDefault();
  const input = $<HTMLInputElement>('task-input');
  const text = input.value.trim();
  if (!text) return;
  const est = Math.max(1, Number($<HTMLInputElement>('task-est').value) || 1);
  store.update((s) => {
    const id = Math.random().toString(36).slice(2, 9);
    s.tasks.push({ id, text, done: false, est, act: 0 });
    if (!s.activeTask) s.activeTask = id;
  });
  input.value = '';
  renderTasks();
});

$('task-list').addEventListener('click', (e) => {
  const el = e.target as HTMLElement;
  const li = el.closest('li');
  const act = el.dataset.act;
  if (!li || !act) return;
  const id = li.dataset.id!;
  store.update((s) => {
    const t = s.tasks.find((x) => x.id === id);
    if (!t) return;
    if (act === 'done') t.done = !t.done;
    if (act === 'select') s.activeTask = id;
    if (act === 'del') {
      s.tasks = s.tasks.filter((x) => x.id !== id);
      if (s.activeTask === id) s.activeTask = null;
    }
  });
  renderTasks();
});

// --------------------------------------------------------------- toast
let toastTimer: ReturnType<typeof setTimeout> | undefined;
function postcard(i: number) {
  return `postcards/region_${String(i).padStart(2, '0')}.jpg`;
}

function toast(title: string, body = '', ms = 5000, img = '') {
  const el = $('toast');
  el.innerHTML = `${img ? `<img class="toast-img" src="${img}" alt="" onerror="this.remove()" />` : ''}<div class="eyebrow"><span>${title}</span></div>${body ? `<div class="body">${body}</div>` : ''}`;
  el.classList.toggle('has-img', Boolean(img));
  el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), ms);
}

// --------------------------------------------------------------- controls
$('btn-start').addEventListener('click', () => {
  blip();
  timer.toggle();
});
$('btn-reset').addEventListener('click', () => {
  if (timer.mode === 'focus' && timer.running && !confirm('Give up on this focus block? Nothing will be built.')) return;
  timer.reset();
});
$('btn-skip').addEventListener('click', () => {
  if (timer.mode === 'focus' && timer.remaining < timer.total && !confirm('Skip this focus block? Nothing will be built.')) return;
  timer.skip();
});
document.querySelectorAll<HTMLButtonElement>('.tabs button').forEach((b) =>
  b.addEventListener('click', () => {
    const mode = b.dataset.mode as Mode;
    if (mode === timer.mode) return;
    if (timer.mode === 'focus' && timer.running && !confirm('Leave this focus block? Nothing will be built.')) return;
    timer.setMode(mode);
  }),
);
$('btn-clawd').addEventListener('click', () => world?.focusClawd());
$('btn-overview').addEventListener('click', () => world?.frameOverview());

window.addEventListener('keydown', (e) => {
  const tag = (e.target as HTMLElement).tagName;
  if (tag === 'INPUT' || tag === 'TEXTAREA' || (e.target as HTMLElement).isContentEditable) return;
  if (e.code === 'Space') {
    e.preventDefault();
    timer.toggle();
  } else if (e.key === 'c') world?.focusClawd();
  else if (e.key === 'o') world?.frameOverview();
  else if (e.key === 'm') fm.toggle($('video'));
  else if (e.key === 'p' && manifest.length) openAlbum();
});

// --------------------------------------------------------------- radio
const vol = $<HTMLInputElement>('vol');
vol.value = String(store.state.volume);
fm.setVolume(store.state.volume);
vol.addEventListener('input', () => {
  const v = Number(vol.value);
  fm.setVolume(v);
  store.update((s) => (s.volume = v));
});
$('btn-play').addEventListener('click', () => fm.toggle($('video')));
$('btn-video').addEventListener('click', () => document.body.classList.toggle('show-video'));
fm.on((st, title) => {
  document.body.dataset.fm = st;
  $('play-icon').setAttribute('d', st === 'playing' ? 'M2 1h2v8H2zM6 1h2v8H6z' : 'M2 1l7 4-7 4z');
  $('btn-play').setAttribute('aria-label', st === 'playing' ? 'Pause Claude FM' : 'Play Claude FM');
  $('fm-title').textContent =
    st === 'loading' ? 'Tuning in…' : st === 'error' ? 'Couldn’t reach YouTube' : title && st !== 'idle' ? title : 'Lo-fi beats to build with';
});

// --------------------------------------------------------------- settings
const dlg = $<HTMLDialogElement>('settings');
const form = dlg.querySelector('form')!;
$('btn-settings').addEventListener('click', () => {
  const s = store.state.settings as unknown as Record<string, number | boolean>;
  for (const el of Array.from(form.elements) as HTMLInputElement[]) {
    if (!el.name || !(el.name in s)) continue;
    if (el.type === 'checkbox') el.checked = Boolean(s[el.name]);
    else el.value = String(s[el.name]);
  }
  dlg.showModal();
});
form.addEventListener('change', async (e) => {
  const el = e.target as HTMLInputElement;
  if (!el.name) return;
  if (el.name === 'notify' && el.checked && 'Notification' in window && Notification.permission !== 'granted') {
    el.checked = (await Notification.requestPermission()) === 'granted';
  }
  store.update((s) => {
    const set = s.settings as unknown as Record<string, number | boolean>;
    set[el.name] = el.type === 'checkbox' ? el.checked : Math.max(Number(el.min) || 1, Number(el.value) || 1);
  });
  if (el.name === 'lowPower') world?.setLowPower(el.checked);
  timer.refreshDuration();
  renderTimer(timer.remaining, durationOf(timer.mode));
});
$('btn-export').addEventListener('click', () => {
  const blob = new Blob([store.export()], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `clawdstudy-${new Date().toISOString().slice(0, 10)}.json`;
  a.click();
  URL.revokeObjectURL(a.href);
});
$<HTMLInputElement>('file-import').addEventListener('change', async (e) => {
  const f = (e.target as HTMLInputElement).files?.[0];
  if (!f) return;
  try {
    store.import(await f.text());
    await world?.setUnlocked(unlockedCount());
    renderAll();
    toast('Progress imported', `${unlockedCount()} places restored.`);
  } catch (err) {
    alert(String(err));
  }
});
$('btn-wipe').addEventListener('click', async () => {
  if (!confirm('Reset the whole world and all history? This cannot be undone. (Export first if unsure.)')) return;
  timer.reset();
  store.reset();
  await world?.setUnlocked(0);
  renderAll();
});

// --------------------------------------------------------------- album
function openAlbum() {
  const n = unlockedCount();
  $('album-count').textContent = `${n + 1} of ${TOTAL + 1}`;
  $('album-grid').innerHTML = manifest
    .map((m) =>
      m.id <= n
        ? `<button type="button" class="card" data-i="${m.id}"><img loading="lazy" src="${postcard(m.id)}" alt="${m.title}" onerror="this.style.visibility='hidden'" /><span>${m.title}</span><small>${m.chapter}</small></button>`
        : `<div class="card locked"><div class="lock">${CLAWD_SVG}</div><span>???</span><small>${m.chapter}</small></div>`,
    )
    .join('');
  $<HTMLDialogElement>('album').showModal();
}
$('btn-album').addEventListener('click', openAlbum);
$('album-grid').addEventListener('click', (e) => {
  const card = (e.target as HTMLElement).closest<HTMLElement>('.card[data-i]');
  if (!card) return;
  const m = manifest[Number(card.dataset.i)];
  $<HTMLImageElement>('photo-img').src = postcard(m.id);
  $('photo-title').innerHTML = `<b>${m.title}</b> · ${m.blurb}`;
  $<HTMLDialogElement>('photo').showModal();
});

// --------------------------------------------------------------- debug
if (DEBUG) {
  $('dbg-range').addEventListener('change', async (e) => {
    const n = Number((e.target as HTMLInputElement).value);
    store.update((s) => (s.completed = n));
    await world?.setUnlocked(n);
    renderWorldCard();
  });
  $('dbg-complete').addEventListener('click', () => onComplete('focus', 25));
  setInterval(() => {
    if (world) $('dbg-stats').textContent = JSON.stringify(world.stats());
  }, 1000);
}

// --------------------------------------------------------------- boot
function renderAll() {
  renderTimer(timer.remaining, timer.total);
  renderTasks();
  renderWorldCard();
}

function escapeHtml(s: string) {
  return s.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]!);
}

primeAudio();
setCaption(timer.mode);
timer.restore();
renderAll();
if (!store.state.seenIntro) {
  const intro = $<HTMLDialogElement>('intro');
  intro.showModal();
  intro.addEventListener('close', () => store.update((s) => (s.seenIntro = true)), { once: true });
}
void bootWorld();
