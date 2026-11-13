// The diorama renderer. Loaded lazily after the UI so the timer is usable instantly.
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import { Clawd, type Accessory, type Clip } from './clawd';
import { cloneGlow, makeRegionMaterials, type RevealUniforms } from './materials';
import { SkyEnv } from './sky';
import { PostFX, type Tier } from './postfx';

export interface RegionMeta {
  id: number;
  file: string;
  chapter: string;
  title: string;
  blurb: string;
  parent: number | null;
  door: number[];
  spot: number[];
  look: number[];
  via: number[][];
  action: Clip;
  acc: Accessory | null;
  focus: number[];
  radius: number;
  lm: { file: string; scale: number; res: number } | null;
}

interface Manifest {
  regions: RegionMeta[];
  center: number[];
  extent: number;
}

interface Animated {
  obj: THREE.Object3D;
  anim: 'spin' | 'bob' | 'pulse';
  axis: 'x' | 'y' | 'z';
  speed: number;
  amp: number;
  base: THREE.Vector3;
  phase: number;
  glowMat?: THREE.MeshBasicMaterial;
}

interface Region {
  meta: RegionMeta;
  group: THREE.Group;
  u: RevealUniforms;
  glow: THREE.MeshBasicMaterial;
  baked: THREE.MeshStandardMaterial;
  nightOnly: THREE.Mesh[];
  anims: Animated[];
  revealing: number; // seconds into reveal, -1 when done
}

export type Mood = 'idle' | 'focus' | 'break';

const v3 = (a: number[]) => new THREE.Vector3(a[0], a[1], a[2]);
const lowPowerFps = 30;
// lightMapIntensity per unit of the bake's encode scale (tuned against the real-time sun)
const LM_GAIN = 0.25;

export class World {
  readonly renderer: THREE.WebGLRenderer;
  readonly scene = new THREE.Scene();
  readonly camera: THREE.PerspectiveCamera;
  readonly controls: OrbitControls;
  private loader: GLTFLoader;
  private manifest!: Manifest;
  private regions = new Map<number, Region>();
  private pending = new Map<number, Promise<THREE.Group>>();
  private clawd!: Clawd;
  private prevT = 0;
  private elapsed = 0;
  private sun: THREE.DirectionalLight;
  private skyEnv: SkyEnv;
  private post: PostFX;
  private tier: Tier = 'high';
  private texLoader = new THREE.TextureLoader();
  private lightmaps = new Map<number, Promise<THREE.Texture | null>>();
  private hemi: THREE.HemisphereLight;
  private sky = new THREE.Color();
  private fog: THREE.Fog;
  private camGoal: { target: THREE.Vector3; dist: number } | null = null;
  private followClawd = false;
  private userTouchedAt = -1e9;
  private running = false;
  private dpr = 1;
  private dprCap = 2;
  private frameTimes: number[] = [];
  private lastFrame = 0;
  private lowPower = false;
  private nightT = -1;
  private shadowDirty = true;
  private mood: Mood = 'idle';
  private here = 0; // region Clawd is at
  private wanderAt = 0;
  private busy = false; // in a scripted sequence (reveal)
  private unlocked = 0;
  onReady: (() => void) | null = null;

  constructor(private canvas: HTMLCanvasElement) {
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.info.autoReset = false; // count every pass of the frame
    this.renderer.toneMapping = THREE.NeutralToneMapping; // keeps the palette's true colours
    this.renderer.toneMappingExposure = 1.0;
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFShadowMap;
    this.renderer.shadowMap.autoUpdate = false;
    this.dprCap = Math.min(window.devicePixelRatio || 1, 2);
    this.dpr = this.dprCap;
    this.renderer.setPixelRatio(this.dpr);

    this.camera = new THREE.PerspectiveCamera(32, 1, 0.5, 400);
    this.camera.position.set(14, 14, 18);

    this.controls = new OrbitControls(this.camera, canvas);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.controls.minDistance = 5;
    this.controls.maxDistance = 95;
    this.controls.maxPolarAngle = Math.PI * 0.47;
    this.controls.minPolarAngle = Math.PI * 0.12;
    this.controls.target.set(0, 0.6, 0);
    this.controls.zoomSpeed = 0.8;
    this.controls.rotateSpeed = 0.6;
    this.controls.addEventListener('start', () => {
      this.userTouchedAt = performance.now();
      this.camGoal = null;
      this.followClawd = false;
    });

    // baked lightmaps carry the sky light now; the hemisphere only lifts moving parts a touch
    this.hemi = new THREE.HemisphereLight(0xfff4e6, 0xb9a78f, 0.35);
    this.scene.add(this.hemi);
    this.sun = new THREE.DirectionalLight(0xfff1dc, 1.9);
    this.sun.castShadow = true;
    this.sun.shadow.mapSize.set(4096, 4096);
    this.sun.shadow.radius = 3;
    this.sun.shadow.bias = -0.0008;
    this.sun.shadow.normalBias = 0.03;
    const sc = this.sun.shadow.camera;
    sc.left = -48;
    sc.right = 48;
    sc.top = 48;
    sc.bottom = -48;
    sc.near = 1;
    sc.far = 160;
    this.scene.add(this.sun, this.sun.target);
    this.fog = new THREE.Fog(0xe9e1d3, 70, 190);
    this.scene.fog = this.fog;
    this.scene.background = this.sky;

    this.loader = new GLTFLoader();
    this.loader.setMeshoptDecoder(MeshoptDecoder);

    this.skyEnv = new SkyEnv(this.renderer);
    this.post = new PostFX(this.renderer, this.scene, this.camera);
    window.addEventListener('resize', () => this.resize());
    document.addEventListener('visibilitychange', () => (document.hidden ? this.stop() : this.start()));
    this.resize();
  }

  // ------------------------------------------------------------------ setup
  async init(unlocked: number) {
    const [manifest, clawdGltf] = await Promise.all([
      fetch('world/world.json').then((r) => r.json() as Promise<Manifest>),
      this.loader.loadAsync('world/clawd.glb'),
    ]);
    this.manifest = manifest;
    this.clawd = new Clawd(clawdGltf);
    this.scene.add(this.clawd.root);
    this.unlocked = Math.min(unlocked, this.maxRegion);
    // load what's unlocked (start + earned), all in parallel
    await Promise.all(
      Array.from({ length: this.unlocked + 1 }, (_, i) => this.addRegion(i, true)),
    );
    this.prefetch(this.unlocked + 1);
    const start = this.meta(this.here);
    this.clawd.place(v3(start.spot), v3(start.look));
    this.clawd.wear(start.acc);
    this.clawd.play(start.action);
    this.frameOverview(true);
    this.updateSky(true);
    this.wanderAt = performance.now() + 9000;
    this.start();
    this.onReady?.();
  }

  get maxRegion() {
    return this.manifest ? this.manifest.regions.length - 1 : 30;
  }

  meta(i: number) {
    return this.manifest.regions[i];
  }

  private loadRegion(i: number): Promise<THREE.Group> {
    if (!this.pending.has(i)) {
      const m = this.meta(i);
      this.pending.set(
        i,
        this.loader.loadAsync(m.file).then((g) => g.scene),
      );
    }
    return this.pending.get(i)!;
  }

  /** Path-traced (Cycles) sky light + bounces, baked in Blender. */
  private loadLightmap(i: number): Promise<THREE.Texture | null> {
    if (!this.lightmaps.has(i)) {
      const lm = this.meta(i).lm;
      this.lightmaps.set(
        i,
        lm
          ? this.texLoader.loadAsync(lm.file).then(
              (t) => {
                t.flipY = false;
                t.colorSpace = THREE.SRGBColorSpace; // stored gamma-encoded for 8-bit precision
                t.channel = 0;
                t.anisotropy = 4;
                return t;
              },
              () => null,
            )
          : Promise.resolve(null),
      );
    }
    return this.lightmaps.get(i)!;
  }

  /** Download + decode the next region during focus so the reveal starts instantly. */
  prefetch(i: number) {
    if (!this.manifest || i > this.maxRegion || i < 0) return;
    void this.loadRegion(i).catch(() => this.pending.delete(i));
    void this.loadLightmap(i);
  }

  private async addRegion(i: number, revealed: boolean) {
    if (this.regions.has(i) || i > this.maxRegion) return this.regions.get(i);
    const [group, lightmap] = await Promise.all([this.loadRegion(i), this.loadLightmap(i)]);
    const { u, baked, solid, glow } = makeRegionMaterials(revealed);
    if (lightmap) {
      baked.lightMap = lightmap;
      baked.userData.lmBase = (this.meta(i).lm?.scale ?? 5) * LM_GAIN;
      baked.lightMapIntensity = baked.userData.lmBase;
    } else {
      baked.envMapIntensity = 1.0;
      baked.userData.lmBase = 0;
    }
    const anims: Animated[] = [];
    const nightOnly: THREE.Mesh[] = [];
    const meshes: THREE.Mesh[] = [];
    group.traverse((o) => {
      if ((o as THREE.Mesh).isMesh) meshes.push(o as THREE.Mesh);
    });
    for (const mesh of meshes) {
      const ud = mesh.userData as Record<string, unknown>;
      const isGlow = ud.part === 'glow' || ud.glow === 1;
      let mat: THREE.Material = isGlow ? glow : ud.part === 'static' && lightmap ? baked : solid;
      if (ud.anim === 'pulse' || ud.night === 1) {
        // own material so it can flicker / fade independently
        const pm = cloneGlow(glow);
        if (ud.night === 1) {
          pm.transparent = true;
          pm.depthWrite = false;
          nightOnly.push(mesh);
        }
        mat = pm;
      }
      mesh.material = mat;
      mesh.castShadow = !isGlow && revealed;
      mesh.receiveShadow = !isGlow;
      if (ud.anim) {
        // re-pivot: wrap the mesh in a group at the authored pivot
        const pivot = new THREE.Group();
        const p = ud.pivot as number[];
        pivot.position.set(p[0], p[1], p[2]);
        mesh.parent!.add(pivot);
        pivot.updateMatrixWorld(true);
        pivot.attach(mesh);
        anims.push({
          obj: pivot,
          anim: ud.anim as Animated['anim'],
          axis: ((ud.axis as string) || 'y') as Animated['axis'],
          speed: Number(ud.speed ?? 1),
          amp: Number(ud.amp ?? 0.1),
          base: pivot.position.clone(),
          phase: i * 1.7,
          glowMat: ud.anim === 'pulse' ? (mat as THREE.MeshBasicMaterial) : undefined,
        });
      }
    }
    const r: Region = { meta: this.meta(i), group, u, glow, baked, nightOnly, anims, revealing: revealed ? -1 : 0 };
    this.regions.set(i, r);
    this.scene.add(group);
    this.applyNightTo(r);
    this.shadowDirty = true;
    return r;
  }

  // -------------------------------------------------------------- behaviour
  setMood(m: Mood) {
    this.mood = m;
    if (this.busy || !this.clawd) return;
    if (m === 'focus') {
      // head home to the desk and get studying
      this.wanderAt = Infinity;
      const pts = this.route(this.here, 0);
      this.here = 0;
      this.clawd.walk(pts, () => {
        this.clawd.face(v3(this.meta(0).look));
        this.clawd.wear('book');
        this.clawd.play('read');
      });
      this.focusOn(v3(this.meta(0).spot).add(new THREE.Vector3(0, 0.8, 0)), 17);
    } else if (m === 'break') {
      this.wanderAt = Infinity;
      this.clawd.wear('headphones');
      this.clawd.play('dance');
    } else {
      this.wanderAt = performance.now() + 6000;
      this.doAction(this.here);
    }
  }

  private doAction(i: number) {
    const m = this.meta(i);
    this.clawd.face(v3(m.look));
    this.clawd.wear(m.acc);
    this.clawd.play(m.action);
  }

  /** Path from Clawd's current region to region b along the region tree. */
  private route(a: number, b: number): THREE.Vector3[] {
    const chain = (n: number) => {
      const out = [n];
      while (this.meta(out[out.length - 1]).parent !== null) out.push(this.meta(out[out.length - 1]).parent!);
      return out;
    };
    const ca = chain(a);
    const cb = chain(b);
    const lca = ca.find((n) => cb.includes(n))!;
    const pts: number[][] = [this.meta(a).spot, this.meta(a).door];
    for (const n of ca.slice(0, ca.indexOf(lca))) {
      const m = this.meta(n);
      pts.push(...[...m.via].reverse(), this.meta(m.parent!).door);
    }
    for (const n of cb.slice(0, cb.indexOf(lca)).reverse()) {
      const m = this.meta(n);
      pts.push(...m.via, m.door);
    }
    pts.push(this.meta(b).spot);
    return pts.map(v3);
  }

  goTo(i: number, then?: () => void) {
    const pts = this.route(this.here, i);
    this.here = i;
    this.followClawd = true;
    this.clawd.walk(pts, () => {
      this.followClawd = false;
      this.doAction(i);
      then?.();
    });
  }

  private wander() {
    const choices = [...this.regions.keys()].filter((k) => k !== this.here && k !== 29);
    if (!choices.length) return;
    // prefer nearby places most of the time
    const here = v3(this.meta(this.here).spot);
    choices.sort((a, b) => v3(this.meta(a).spot).distanceTo(here) - v3(this.meta(b).spot).distanceTo(here));
    const pick = choices[Math.floor(Math.random() ** 2 * Math.min(choices.length, 6))];
    this.goTo(pick);
    this.wanderAt = performance.now() + 22000 + Math.random() * 14000;
  }

  /** A focus block finished: build region i with fanfare. Resolves when the show is over. */
  async reveal(i: number): Promise<void> {
    if (i > this.maxRegion || this.regions.has(i)) return;
    this.busy = true;
    this.unlocked = Math.max(this.unlocked, i);
    const r = (await this.addRegion(i, false))!;
    const m = r.meta;
    this.focusOn(v3(m.focus), Math.max(17, m.radius * 3.0));
    await wait(650);
    r.revealing = 0.0001;
    this.clawd.play('look');
    await wait(1900);
    await new Promise<void>((res) => this.goTo(i, res));
    this.clawd.wear(i === 30 ? 'partyhat' : m.acc);
    this.clawd.play(i % 6 === 0 ? 'celebrate' : m.action);
    this.prefetch(i + 1);
    this.busy = false;
    this.wanderAt = performance.now() + 25000;
    if (this.mood === 'break') {
      await wait(4500);
      if (this.mood === 'break' && !this.busy) {
        this.clawd.wear('headphones');
        this.clawd.play('dance');
      }
    }
  }

  /** Debug / import: show exactly regions 0..n with no animation. */
  async setUnlocked(n: number) {
    n = Math.max(0, Math.min(n, this.maxRegion));
    for (const [k, r] of this.regions) {
      if (k > n) {
        this.scene.remove(r.group);
        this.regions.delete(k);
        this.pending.delete(k); // its meshes were re-parented; parse a fresh copy next time
      }
    }
    await Promise.all(Array.from({ length: n + 1 }, (_, i) => this.addRegion(i, true)));
    this.unlocked = n;
    if (this.here > n) {
      this.here = 0;
      this.clawd.place(v3(this.meta(0).spot), v3(this.meta(0).look));
    }
    this.shadowDirty = true;
    this.prefetch(n + 1);
  }

  // ---------------------------------------------------------------- camera
  focusOn(target: THREE.Vector3, dist: number) {
    this.camGoal = { target: target.clone(), dist };
    this.followClawd = false;
  }

  frameOverview(instant = false) {
    // frame everything unlocked so far
    const box = new THREE.Box3();
    for (const r of this.regions.values()) box.expandByPoint(v3(r.meta.focus));
    const c = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3()).length();
    const dist = Math.max(24, size * 1.0 + 14);
    if (instant) {
      this.controls.target.copy(c);
      const dir = new THREE.Vector3(0.55, 0.62, 0.95).normalize();
      this.camera.position.copy(c).addScaledVector(dir, dist);
      this.controls.update();
    } else this.focusOn(c, dist);
  }

  focusClawd() {
    this.focusOn(this.clawd.root.position.clone().add(new THREE.Vector3(0, 0.6, 0)), 10);
    this.followClawd = true;
  }

  private updateCamera(dt: number) {
    const k = 1 - Math.exp(-dt * 2.4);
    if (this.followClawd && this.clawd) {
      const t = this.clawd.root.position.clone().add(new THREE.Vector3(0, 0.6, 0));
      this.camGoal = { target: t, dist: this.camGoal?.dist ?? 15 };
    }
    if (this.camGoal) {
      const off = this.camera.position.clone().sub(this.controls.target);
      const len = off.length();
      this.controls.target.lerp(this.camGoal.target, k);
      const newLen = len + (this.camGoal.dist - len) * k;
      this.camera.position.copy(this.controls.target).addScaledVector(off.normalize(), newLen);
      if (!this.followClawd && this.controls.target.distanceTo(this.camGoal.target) < 0.02 && Math.abs(newLen - this.camGoal.dist) < 0.05)
        this.camGoal = null;
    }
    // gentle drift while nobody is touching the controls
    const idle = performance.now() - this.userTouchedAt > 12000;
    this.controls.autoRotate = idle;
    this.controls.autoRotateSpeed = this.mood === 'focus' ? 0.12 : 0.25;
    this.controls.update(dt);
  }

  // --------------------------------------------------------------- day/night
  private updateSky(force = false) {
    const now = new Date();
    const h = now.getHours() + now.getMinutes() / 60;
    const forced = new URLSearchParams(location.search).get('time');
    const hour = forced ? Number(forced) : h;
    // 0 = day, 1 = deep night, smooth dusk/dawn
    const night =
      hour < 5 ? 1 : hour < 7.5 ? 1 - (hour - 5) / 2.5 : hour < 18 ? 0 : hour < 20.5 ? (hour - 18) / 2.5 : 1;
    if (!force && Math.abs(night - this.nightT) < 0.005) return;
    this.nightT = night;
    document.body.dataset.night = night > 0.55 ? '1' : '0';
    const day = new THREE.Color(0xe9e1d3);
    const dusk = new THREE.Color(0xe3b49a);
    const deep = new THREE.Color(0x1d2233);
    const sky = night < 0.5 ? day.clone().lerp(dusk, night * 2) : dusk.clone().lerp(deep, (night - 0.5) * 2);
    this.sky.copy(sky);
    this.fog.color.copy(sky);
    this.hemi.intensity = THREE.MathUtils.lerp(0.35, 0.25, night);
    this.hemi.color.set(night > 0.5 ? 0x9fb2e6 : 0xfff4e6);
    this.hemi.groundColor.set(night > 0.5 ? 0x3b3550 : 0xb9a78f);
    this.sun.intensity = THREE.MathUtils.lerp(3.5, 0.55, night);
    this.sun.color.set(night > 0.5 ? 0xa9bdff : night > 0.1 ? 0xffd2a6 : 0xfff1dc);
    const ang = THREE.MathUtils.lerp(0.9, 0.55, night);
    this.sun.position.set(Math.cos(ang) * 40, 60, Math.sin(ang) * 50);
    this.sun.target.position.set(0, 0, 0);
    const env = this.skyEnv.update(night, this.sun.position);
    if (env) this.scene.environment = env;
    this.post.setNight(night);
    for (const r of this.regions.values()) this.applyNightTo(r);
    this.shadowDirty = true;
  }

  private applyNightTo(r: Region) {
    const n = Math.max(0, this.nightT);
    // HDR glow at night so bloom picks up windows and lamps
    r.glow.color.setScalar(THREE.MathUtils.lerp(0.9, 2.6, n));
    r.baked.lightMapIntensity = (r.baked.userData.lmBase as number) * THREE.MathUtils.lerp(1, 0.22, n);
    // aurora + stars only come out after dusk
    const vis = THREE.MathUtils.smoothstep(n, 0.35, 0.9);
    for (const m of r.nightOnly) {
      (m.material as THREE.MeshBasicMaterial).opacity = vis * 0.85;
      m.visible = vis > 0.01;
    }
  }

  // ----------------------------------------------------------------- loop
  start() {
    if (this.running || document.hidden) return;
    this.running = true;
    this.prevT = performance.now();
    this.renderer.setAnimationLoop((t) => this.frame(t));
  }

  stop() {
    this.running = false;
    this.renderer.setAnimationLoop(null);
  }

  setLowPower(on: boolean) {
    this.lowPower = on;
    this.renderer.shadowMap.enabled = !on;
    this.dpr = on ? 1 : this.dprCap;
    this.setTier(on ? 'low' : 'high');
    this.shadowDirty = true;
    this.resize();
  }

  private setTier(t: Tier) {
    this.tier = t;
    this.post.setTier(t);
  }

  private frame(t: number) {
    if (this.lowPower && t - this.lastFrame < 1000 / lowPowerFps - 2) return;
    const frameMs = t - this.lastFrame;
    this.lastFrame = t;
    const now = performance.now();
    const dt = Math.min((now - this.prevT) / 1000, 1 / 20);
    this.prevT = now;
    this.elapsed += dt;
    const time = this.elapsed;

    // regions: reveal + ambient animation
    for (const r of this.regions.values()) {
      if (r.revealing >= 0) {
        r.revealing += dt;
        const p = Math.min(1, r.revealing / 2.2);
        r.u.uReveal.value = p;
        if (p >= 1) {
          r.revealing = -1;
          r.group.traverse((o) => {
            const m = o as THREE.Mesh;
            if (m.isMesh && m.receiveShadow) m.castShadow = true;
          });
          this.shadowDirty = true;
        }
      }
      for (const a of r.anims) {
        if (a.anim === 'spin') a.obj.rotation[a.axis] = time * a.speed + a.phase;
        else if (a.anim === 'bob') a.obj.position.y = a.base.y + Math.sin(time * a.speed * 2 + a.phase) * a.amp;
        else if (a.anim === 'pulse' && a.glowMat) {
          const s = 0.75 + 0.25 * Math.sin(time * a.speed * 2 + a.phase);
          a.glowMat.color.setScalar(s);
        }
      }
    }

    if (this.clawd) {
      this.clawd.update(dt);
      if (!this.busy && !this.clawd.walking && this.mood === 'idle' && performance.now() > this.wanderAt) this.wander();
    }
    if ((time | 0) % 30 === 0) this.updateSky();
    this.updateCamera(dt);

    if (this.shadowDirty && this.renderer.shadowMap.enabled) {
      this.renderer.shadowMap.needsUpdate = true;
      this.shadowDirty = false;
    }
    this.renderer.info.reset();
    this.post.render(dt, time);
    this.adapt(frameMs);
  }

  /** Drop resolution if frames are slow, restore it when there's headroom. */
  private adapt(ms: number) {
    if (this.lowPower || ms <= 0 || ms > 250) return;
    this.frameTimes.push(ms);
    if (this.frameTimes.length < 90) return;
    const avg = this.frameTimes.reduce((a, b) => a + b, 0) / this.frameTimes.length;
    this.frameTimes.length = 0;
    // first trade resolution, then effects; climb back the same way
    let next = this.dpr;
    if (avg > 20) {
      if (this.dpr > 1) next = Math.max(1, this.dpr - 0.25);
      else if (this.tier === 'high') this.setTier('medium');
      else if (this.tier === 'medium') this.setTier('low');
    } else if (avg < 12) {
      if (this.tier === 'low') this.setTier('medium');
      else if (this.tier === 'medium') this.setTier('high');
      else if (this.dpr < this.dprCap) next = Math.min(this.dprCap, this.dpr + 0.25);
    }
    if (next !== this.dpr) {
      this.dpr = next;
      this.resize();
    }
  }

  resize() {
    const w = this.canvas.clientWidth || window.innerWidth;
    const h = this.canvas.clientHeight || window.innerHeight;
    this.renderer.setPixelRatio(this.dpr);
    this.renderer.setSize(w, h, false);
    this.post?.setSize(w, h, this.dpr);
    this.camera.aspect = w / h;
    this.camera.fov = w < 700 ? 42 : 32;
    this.camera.updateProjectionMatrix();
  }

  stats() {
    const i = this.renderer.info;
    return { calls: i.render.calls, triangles: i.render.triangles, geometries: i.memory.geometries, dpr: this.dpr, tier: this.tier };
  }
}

function wait(ms: number) {
  return new Promise<void>((r) => setTimeout(r, ms));
}
