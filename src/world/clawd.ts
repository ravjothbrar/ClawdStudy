// Clawd: the Blender-exported rig, its baked animation clips, accessories and
// a simple path follower for walking around the archipelago.
import * as THREE from 'three';
import type { GLTF } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { clawdMaterial } from './materials';

export type Clip = 'idle' | 'walk' | 'dance' | 'read' | 'sip' | 'hammer' | 'wave' | 'sleep' | 'celebrate' | 'look';
export type Accessory = 'headphones' | 'hardhat' | 'goggles' | 'mug' | 'book' | 'hammer' | 'partyhat' | 'nightcap';

const WALK_SPEED = 2.6; // units / second
const MAX_WALK_TIME = 9; // long trips speed up so nobody waits forever

export class Clawd {
  readonly root = new THREE.Group();
  private mixer: THREE.AnimationMixer;
  private actions = new Map<string, THREE.AnimationAction>();
  private current: THREE.AnimationAction | null = null;
  private acc = new Map<string, THREE.Object3D>();
  private path: THREE.Vector3[] = [];
  private seg = 0;
  private segT = 0;
  private speed = WALK_SPEED;
  private yaw = 0;
  private targetYaw = 0;
  private onArrive: (() => void) | null = null;
  private shadow: THREE.Mesh;
  walking = false;

  constructor(gltf: GLTF) {
    const model = gltf.scene;
    model.traverse((o) => {
      const m = o as THREE.Mesh;
      if (m.isMesh) {
        m.material = clawdMaterial;
        m.castShadow = false;
        m.frustumCulled = false;
        const name = (m.userData.accessory as string) || (m.name.startsWith('acc_') ? m.name.slice(4) : '');
        if (name) {
          this.acc.set(name, m);
          m.visible = false;
        }
      }
    });
    this.root.add(model);
    this.mixer = new THREE.AnimationMixer(model);
    for (const clip of gltf.animations) {
      const a = this.mixer.clipAction(clip);
      if (clip.name === 'celebrate' || clip.name === 'hammer' || clip.name === 'wave') {
        // one-shots loop too, but feel punchier slightly faster
        a.timeScale = 1.0;
      }
      this.actions.set(clip.name, a);
    }
    // cheap blob shadow (the world's shadow map is static)
    const c = document.createElement('canvas');
    c.width = c.height = 64;
    const g = c.getContext('2d')!;
    const grd = g.createRadialGradient(32, 32, 4, 32, 32, 32);
    grd.addColorStop(0, 'rgba(30,22,16,0.62)');
    grd.addColorStop(0.55, 'rgba(30,22,16,0.32)');
    grd.addColorStop(1, 'rgba(30,22,16,0)');
    g.fillStyle = grd;
    g.fillRect(0, 0, 64, 64);
    this.shadow = new THREE.Mesh(
      new THREE.PlaneGeometry(1.9, 1.2),
      new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(c), transparent: true, depthWrite: false }),
    );
    this.shadow.rotation.x = -Math.PI / 2;
    this.shadow.position.y = 0.02;
    this.shadow.renderOrder = 1;
    this.root.add(this.shadow);
    this.play('idle');
  }

  play(name: Clip, fade = 0.25) {
    const next = this.actions.get(name) ?? this.actions.get('idle')!;
    if (next === this.current) return;
    next.reset().setEffectiveWeight(1).fadeIn(fade).play();
    this.current?.fadeOut(fade);
    this.current = next;
  }

  wear(name: Accessory | null) {
    this.acc.forEach((o, k) => (o.visible = k === name));
  }

  place(p: THREE.Vector3, lookAt?: THREE.Vector3) {
    this.root.position.copy(p);
    if (lookAt) this.face(lookAt, true);
  }

  face(p: THREE.Vector3, instant = false) {
    const d = p.clone().sub(this.root.position);
    if (d.lengthSq() < 1e-6) return;
    this.targetYaw = Math.atan2(d.x, d.z);
    if (instant) this.yaw = this.targetYaw;
  }

  walk(points: THREE.Vector3[], onArrive?: () => void) {
    const pts = [this.root.position.clone(), ...points].filter(
      (p, i, a) => i === 0 || p.distanceToSquared(a[i - 1]) > 1e-4,
    );
    if (pts.length < 2) {
      onArrive?.();
      return;
    }
    let len = 0;
    for (let i = 1; i < pts.length; i++) len += pts[i].distanceTo(pts[i - 1]);
    this.speed = Math.max(WALK_SPEED, len / MAX_WALK_TIME);
    this.path = pts;
    this.seg = 0;
    this.segT = 0;
    this.walking = true;
    this.onArrive = onArrive ?? null;
    this.wear(null);
    this.play('walk', 0.15);
    const walkAction = this.actions.get('walk');
    if (walkAction) walkAction.timeScale = Math.min(2.2, this.speed / WALK_SPEED);
  }

  update(dt: number) {
    if (this.walking) {
      let move = this.speed * dt;
      while (move > 0 && this.seg < this.path.length - 1) {
        const a = this.path[this.seg];
        const b = this.path[this.seg + 1];
        const segLen = a.distanceTo(b);
        const left = segLen * (1 - this.segT);
        if (move >= left) {
          move -= left;
          this.seg++;
          this.segT = 0;
        } else {
          this.segT += move / segLen;
          move = 0;
        }
      }
      if (this.seg >= this.path.length - 1) {
        this.root.position.copy(this.path[this.path.length - 1]);
        this.walking = false;
        const cb = this.onArrive;
        this.onArrive = null;
        cb?.();
      } else {
        const a = this.path[this.seg];
        const b = this.path[this.seg + 1];
        this.root.position.lerpVectors(a, b, this.segT);
        const dx = b.x - a.x;
        const dz = b.z - a.z;
        if (dx * dx + dz * dz > 1e-6) this.targetYaw = Math.atan2(dx, dz);
      }
    }
    // smooth turning
    let d = this.targetYaw - this.yaw;
    d = Math.atan2(Math.sin(d), Math.cos(d));
    this.yaw += d * Math.min(1, dt * 8);
    this.root.rotation.y = this.yaw;
    this.mixer.update(dt);
  }
}
