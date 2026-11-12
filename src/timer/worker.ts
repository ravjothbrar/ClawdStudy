// A tiny ticker. Workers are throttled far less than main-thread timers in
// background tabs, so the countdown (and the completion chime) stays on time.
let id: ReturnType<typeof setInterval> | null = null;

self.onmessage = (e: MessageEvent<'start' | 'stop'>) => {
  if (e.data === 'start' && id === null) {
    id = setInterval(() => (self as unknown as Worker).postMessage(Date.now()), 250);
  } else if (e.data === 'stop' && id !== null) {
    clearInterval(id);
    id = null;
  }
};
