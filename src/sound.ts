// Synthesised chimes: no audio files to download.
let ctx: AudioContext | null = null;

function ac() {
  ctx ??= new AudioContext();
  if (ctx.state === 'suspended') void ctx.resume();
  return ctx;
}

function bell(freq: number, at: number, dur = 1.2, gain = 0.18) {
  const c = ac();
  const t = c.currentTime + at;
  const o = c.createOscillator();
  const o2 = c.createOscillator();
  const g = c.createGain();
  o.type = 'sine';
  o2.type = 'triangle';
  o.frequency.value = freq;
  o2.frequency.value = freq * 2;
  g.gain.setValueAtTime(0, t);
  g.gain.linearRampToValueAtTime(gain, t + 0.01);
  g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
  const g2 = c.createGain();
  g2.gain.value = 0.25;
  o.connect(g);
  o2.connect(g2).connect(g);
  g.connect(c.destination);
  o.start(t);
  o2.start(t);
  o.stop(t + dur);
  o2.stop(t + dur);
}

/** Bright arpeggio: a focus block is done and something new was built. */
export function chimeBuild() {
  [523.25, 659.25, 783.99, 1046.5].forEach((f, i) => bell(f, i * 0.11, 1.4));
}

/** Soft two-note: a break is over. */
export function chimeBreak() {
  bell(659.25, 0, 1.0, 0.14);
  bell(523.25, 0.18, 1.2, 0.14);
}

/** Tiny tick for button presses. */
export function blip() {
  bell(880, 0, 0.12, 0.05);
}

/** Unlock the audio context on the first user gesture. */
export function primeAudio() {
  const go = () => {
    ac();
    window.removeEventListener('pointerdown', go);
    window.removeEventListener('keydown', go);
  };
  window.addEventListener('pointerdown', go);
  window.addEventListener('keydown', go);
}
