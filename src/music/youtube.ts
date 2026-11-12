// Claude FM via the YouTube IFrame Player API.
// The API and iframe are only loaded when the user first presses play, so the
// stream can never compete with the 3D scene for bandwidth on page load.

export const CLAUDE_FM_ID = 'tRsQsTMvPNg';

interface YTPlayer {
  playVideo(): void;
  pauseVideo(): void;
  setVolume(v: number): void;
  getPlayerState(): number;
  getVideoData?(): { title?: string };
}

declare global {
  interface Window {
    YT?: { Player: new (el: HTMLElement, opts: unknown) => YTPlayer; PlayerState: Record<string, number> };
    onYouTubeIframeAPIReady?: () => void;
  }
}

type State = 'idle' | 'loading' | 'playing' | 'paused' | 'error';
type Listener = (s: State, title?: string) => void;

class ClaudeFM {
  state: State = 'idle';
  private player: YTPlayer | null = null;
  private ready: Promise<YTPlayer> | null = null;
  private listeners = new Set<Listener>();
  private volume = 60;
  title = 'Claude FM, live';

  on(fn: Listener) {
    this.listeners.add(fn);
    fn(this.state, this.title);
    return () => this.listeners.delete(fn);
  }

  private set(s: State) {
    this.state = s;
    this.listeners.forEach((l) => l(s, this.title));
  }

  private load(host: HTMLElement): Promise<YTPlayer> {
    if (this.ready) return this.ready;
    this.set('loading');
    this.ready = new Promise<YTPlayer>((resolve, reject) => {
      const create = () => {
        const el = document.createElement('div');
        host.appendChild(el);
        const p = new window.YT!.Player(el, {
          videoId: CLAUDE_FM_ID,
          width: '100%',
          height: '100%',
          playerVars: { autoplay: 1, controls: 0, disablekb: 1, modestbranding: 1, playsinline: 1, rel: 0 },
          events: {
            onReady: () => {
              p.setVolume(this.volume);
              const t = p.getVideoData?.().title;
              if (t) this.title = t;
              resolve(p);
            },
            onStateChange: (e: { data: number }) => {
              if (e.data === 1) this.set('playing');
              else if (e.data === 2 || e.data === 0) this.set('paused');
            },
            onError: () => {
              this.set('error');
              reject(new Error('YouTube player error'));
            },
          },
        });
        this.player = p;
      };
      if (window.YT?.Player) return create();
      const prev = window.onYouTubeIframeAPIReady;
      window.onYouTubeIframeAPIReady = () => {
        prev?.();
        create();
      };
      const s = document.createElement('script');
      s.src = 'https://www.youtube.com/iframe_api';
      s.async = true;
      s.onerror = () => {
        this.set('error');
        reject(new Error('Could not load YouTube'));
      };
      document.head.appendChild(s);
    });
    return this.ready;
  }

  async play(host: HTMLElement) {
    try {
      const p = await this.load(host);
      p.playVideo();
    } catch {
      this.set('error');
    }
  }

  pause() {
    this.player?.pauseVideo();
  }

  toggle(host: HTMLElement) {
    if (this.state === 'playing') this.pause();
    else void this.play(host);
  }

  setVolume(v: number) {
    this.volume = v;
    this.player?.setVolume(v);
  }
}

export const fm = new ClaudeFM();
