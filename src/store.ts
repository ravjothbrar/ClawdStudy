// Local-first persistence. Everything lives in localStorage; nothing leaves the browser.

export interface Settings {
  focusMin: number;
  shortMin: number;
  longMin: number;
  longEvery: number;
  autoBreaks: boolean;
  autoFocus: boolean;
  sound: boolean;
  notify: boolean;
  musicOnFocus: boolean;
  lowPower: boolean;
}

export interface Task {
  id: string;
  text: string;
  done: boolean;
  est: number;
  act: number;
}

export interface Session {
  t: number; // completion time (ms)
  min: number;
  region: number | null; // region unlocked by this session
}

export interface TimerSnapshot {
  mode: Mode;
  endAt: number | null; // running if set
  remaining: number; // ms, used when paused
  cycle: number; // completed focus blocks in the current long-break cycle
}

export type Mode = 'focus' | 'short' | 'long';

export interface State {
  v: 1;
  completed: number; // total completed pomodoros (drives the world)
  history: Session[];
  tasks: Task[];
  activeTask: string | null;
  settings: Settings;
  timer: TimerSnapshot;
  seenIntro: boolean;
  volume: number;
}

export const DEFAULT_SETTINGS: Settings = {
  focusMin: 25,
  shortMin: 5,
  longMin: 15,
  longEvery: 4,
  autoBreaks: false,
  autoFocus: false,
  sound: true,
  notify: false,
  musicOnFocus: true,
  lowPower: false,
};

const KEY = 'clawdstudy:v1';

function fresh(): State {
  return {
    v: 1,
    completed: 0,
    history: [],
    tasks: [],
    activeTask: null,
    settings: { ...DEFAULT_SETTINGS },
    timer: { mode: 'focus', endAt: null, remaining: DEFAULT_SETTINGS.focusMin * 60_000, cycle: 0 },
    seenIntro: false,
    volume: 60,
  };
}

function load(): State {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return fresh();
    const s = JSON.parse(raw) as Partial<State>;
    const base = fresh();
    return {
      ...base,
      ...s,
      settings: { ...base.settings, ...(s.settings ?? {}) },
      timer: { ...base.timer, ...(s.timer ?? {}) },
    } as State;
  } catch {
    return fresh();
  }
}

type Listener = (s: State) => void;

class Store {
  state: State = load();
  private listeners = new Set<Listener>();
  private saveQueued = false;

  subscribe(fn: Listener) {
    this.listeners.add(fn);
    return () => this.listeners.delete(fn);
  }

  update(fn: (s: State) => void) {
    fn(this.state);
    this.listeners.forEach((l) => l(this.state));
    this.queueSave();
  }

  private queueSave() {
    if (this.saveQueued) return;
    this.saveQueued = true;
    queueMicrotask(() => {
      this.saveQueued = false;
      try {
        localStorage.setItem(KEY, JSON.stringify(this.state));
      } catch {
        /* storage full or blocked: keep running in memory */
      }
    });
  }

  export(): string {
    return JSON.stringify(this.state, null, 1);
  }

  import(json: string) {
    const s = JSON.parse(json) as State;
    if (s.v !== 1 || typeof s.completed !== 'number') throw new Error('Not a ClawdStudy save');
    localStorage.setItem(KEY, JSON.stringify(s));
    this.state = load();
    this.listeners.forEach((l) => l(this.state));
  }

  reset() {
    this.state = fresh();
    this.state.seenIntro = true;
    this.listeners.forEach((l) => l(this.state));
    this.queueSave();
  }
}

export const store = new Store();

export function todayCount(s: State) {
  const start = new Date();
  start.setHours(0, 0, 0, 0);
  return s.history.filter((h) => h.t >= start.getTime()).length;
}

export function streakDays(s: State) {
  const days = new Set(s.history.map((h) => new Date(h.t).toDateString()));
  let n = 0;
  const d = new Date();
  if (!days.has(d.toDateString())) d.setDate(d.getDate() - 1);
  while (days.has(d.toDateString())) {
    n++;
    d.setDate(d.getDate() - 1);
  }
  return n;
}
