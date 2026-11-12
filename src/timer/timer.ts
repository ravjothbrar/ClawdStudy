// Pomodoro state machine. Time is derived from a stored end timestamp, never from
// counting ticks, so it cannot drift and survives reloads.
import { store, type Mode } from '../store';

export type TimerEvent =
  | { type: 'tick'; remaining: number; total: number }
  | { type: 'start'; mode: Mode }
  | { type: 'pause'; mode: Mode }
  | { type: 'mode'; mode: Mode }
  | { type: 'complete'; mode: Mode; minutes: number }
  | { type: 'abandon'; mode: Mode; elapsed: number };

type Listener = (e: TimerEvent) => void;

// ?fast=5 makes every block 5 seconds long (for demos and tests)
const FAST = Number(new URLSearchParams(location.search).get('fast')) || 0;

export function durationOf(mode: Mode) {
  if (FAST) return FAST * 1000;
  const s = store.state.settings;
  const min = mode === 'focus' ? s.focusMin : mode === 'short' ? s.shortMin : s.longMin;
  return min * 60_000;
}

class Timer {
  private listeners = new Set<Listener>();
  private worker: Worker | null = null;
  private fallback: ReturnType<typeof setInterval> | null = null;

  constructor() {
    try {
      this.worker = new Worker(new URL('./worker.ts', import.meta.url), { type: 'module' });
      this.worker.onmessage = () => this.tick();
    } catch {
      this.worker = null;
    }
    document.addEventListener('visibilitychange', () => this.tick());
  }

  on(fn: Listener) {
    this.listeners.add(fn);
    return () => this.listeners.delete(fn);
  }

  private emit(e: TimerEvent) {
    this.listeners.forEach((l) => l(e));
  }

  get mode() {
    return store.state.timer.mode;
  }
  get running() {
    return store.state.timer.endAt !== null;
  }
  get remaining() {
    const t = store.state.timer;
    return t.endAt !== null ? Math.max(0, t.endAt - Date.now()) : t.remaining;
  }
  get total() {
    return durationOf(this.mode);
  }

  /** Call once on boot: resumes a running timer or completes one that ended while away. */
  restore() {
    const t = store.state.timer;
    if (t.remaining > this.total || t.remaining <= 0) {
      store.update((s) => (s.timer.remaining = this.total));
    }
    if (t.endAt !== null) {
      this.startTicking();
      this.tick();
    } else {
      this.emitTick();
    }
  }

  start() {
    if (this.running) return;
    const rem = this.remaining > 0 ? this.remaining : this.total;
    store.update((s) => {
      s.timer.endAt = Date.now() + rem;
    });
    this.startTicking();
    this.emit({ type: 'start', mode: this.mode });
    this.emitTick();
  }

  pause() {
    if (!this.running) return;
    const rem = this.remaining;
    store.update((s) => {
      s.timer.endAt = null;
      s.timer.remaining = rem;
    });
    this.stopTicking();
    this.emit({ type: 'pause', mode: this.mode });
    this.emitTick();
  }

  toggle() {
    this.running ? this.pause() : this.start();
  }

  /** Give up on the current block. A focus block abandoned this way builds nothing. */
  reset() {
    const mode = this.mode;
    const elapsed = this.total - this.remaining;
    this.stopTicking();
    store.update((s) => {
      s.timer.endAt = null;
      s.timer.remaining = this.total;
    });
    if (elapsed > 1000) this.emit({ type: 'abandon', mode, elapsed });
    this.emitTick();
  }

  setMode(mode: Mode, autostart = false) {
    this.stopTicking();
    store.update((s) => {
      s.timer.mode = mode;
      s.timer.endAt = null;
      s.timer.remaining = durationOf(mode);
    });
    this.emit({ type: 'mode', mode });
    this.emitTick();
    if (autostart) this.start();
  }

  /** Skip straight to the end of a break (focus blocks can't be skipped for credit). */
  skip() {
    if (this.mode === 'focus') {
      this.reset();
      this.setMode(this.nextBreak());
    } else {
      this.setMode('focus', store.state.settings.autoFocus);
    }
  }

  /** Re-read durations after the settings change (only affects a block that hasn't started). */
  refreshDuration() {
    if (!this.running && this.remaining === store.state.timer.remaining) {
      store.update((s) => (s.timer.remaining = durationOf(s.timer.mode)));
      this.emitTick();
    }
  }

  private nextBreak(): Mode {
    const s = store.state;
    return s.timer.cycle > 0 && s.timer.cycle % s.settings.longEvery === 0 ? 'long' : 'short';
  }

  private tick() {
    if (!this.running) return;
    if (this.remaining <= 0) {
      this.finish();
      return;
    }
    this.emitTick();
  }

  private finish() {
    const mode = this.mode;
    this.stopTicking();
    const minutes = Math.round(durationOf(mode) / 60_000);
    if (mode === 'focus') {
      store.update((s) => {
        s.timer.cycle += 1;
      });
    }
    store.update((s) => {
      s.timer.endAt = null;
      s.timer.remaining = 0;
    });
    this.emit({ type: 'complete', mode, minutes });
    const st = store.state.settings;
    if (mode === 'focus') this.setMode(this.nextBreak(), st.autoBreaks);
    else {
      if (mode === 'long') store.update((s) => (s.timer.cycle = 0));
      this.setMode('focus', st.autoFocus);
    }
  }

  private emitTick() {
    this.emit({ type: 'tick', remaining: this.remaining, total: this.total });
  }

  private startTicking() {
    if (this.worker) this.worker.postMessage('start');
    else if (!this.fallback) this.fallback = setInterval(() => this.tick(), 250);
  }

  private stopTicking() {
    this.worker?.postMessage('stop');
    if (this.fallback) clearInterval(this.fallback);
    this.fallback = null;
  }
}

export const timer = new Timer();

export function fmt(ms: number) {
  const total = Math.ceil(ms / 1000);
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}
