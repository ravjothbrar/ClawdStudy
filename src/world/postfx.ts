// Post-processing for the "photographed miniature" look, in quality tiers:
//   high   : MSAA -> tilt-shift lens -> bloom -> AgX output -> sharpen/vignette/grain
//   medium : MSAA -> bloom (night only) -> AgX output -> sharpen/vignette/grain
//   low    : plain renderer.render (tone mapping in the main shader), no extras
import * as THREE from 'three';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { ShaderPass } from 'three/examples/jsm/postprocessing/ShaderPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js';

export type Tier = 'high' | 'medium' | 'low';

const TiltShift = {
  uniforms: {
    tDiffuse: { value: null as THREE.Texture | null },
    uStep: { value: new THREE.Vector2() },
    uFocus: { value: 0.47 },
    uBand: { value: 0.24 },
    uAmount: { value: 2.6 },
  },
  vertexShader: /* glsl */ `
    varying vec2 vUv;
    void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
  fragmentShader: /* glsl */ `
    uniform sampler2D tDiffuse;
    uniform vec2 uStep;
    uniform float uFocus, uBand, uAmount;
    varying vec2 vUv;
    void main() {
      float k = smoothstep(uBand, uBand + 0.38, abs(vUv.y - uFocus)) * uAmount;
      if (k < 0.05) { gl_FragColor = texture2D(tDiffuse, vUv); return; }
      vec2 s = uStep * k;
      vec4 c = texture2D(tDiffuse, vUv) * 0.2270270270;
      c += (texture2D(tDiffuse, vUv + s * 1.3846153846) + texture2D(tDiffuse, vUv - s * 1.3846153846)) * 0.3162162162;
      c += (texture2D(tDiffuse, vUv + s * 3.2307692308) + texture2D(tDiffuse, vUv - s * 3.2307692308)) * 0.0702702703;
      gl_FragColor = c;
    }`,
};

const Finish = {
  uniforms: {
    tDiffuse: { value: null as THREE.Texture | null },
    uTexel: { value: new THREE.Vector2() },
    uTime: { value: 0 },
    uSharpen: { value: 0.32 },
    uVignette: { value: 0.2 },
    uGrain: { value: 0.016 },
  },
  vertexShader: TiltShift.vertexShader,
  fragmentShader: /* glsl */ `
    uniform sampler2D tDiffuse;
    uniform vec2 uTexel;
    uniform float uTime, uSharpen, uVignette, uGrain;
    varying vec2 vUv;
    float hash(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
    void main() {
      vec3 c = texture2D(tDiffuse, vUv).rgb;
      // contrast-adaptive sharpening (lite): pull edges apart, less where contrast is already high
      vec3 n = texture2D(tDiffuse, vUv + vec2(0.0, uTexel.y)).rgb;
      vec3 s = texture2D(tDiffuse, vUv - vec2(0.0, uTexel.y)).rgb;
      vec3 e = texture2D(tDiffuse, vUv + vec2(uTexel.x, 0.0)).rgb;
      vec3 w = texture2D(tDiffuse, vUv - vec2(uTexel.x, 0.0)).rgb;
      vec3 mn = min(c, min(min(n, s), min(e, w)));
      vec3 mx = max(c, max(max(n, s), max(e, w)));
      vec3 amp = clamp(min(mn, 1.0 - mx) / max(mx, 1e-3), 0.0, 1.0);
      vec3 wgt = sqrt(amp) * uSharpen;
      c = clamp((c * (1.0 + 4.0 * wgt) - (n + s + e + w) * wgt), 0.0, 1.0);
      // lens vignette
      vec2 q = vUv - 0.5;
      c *= 1.0 - uVignette * smoothstep(0.25, 0.95, dot(q, q) * 2.2);
      // fine film grain
      c += (hash(vUv * 1024.0 + uTime) - 0.5) * uGrain;
      gl_FragColor = vec4(c, 1.0);
    }`,
};

export class PostFX {
  tier: Tier = 'high';
  private composer: EffectComposer;
  private tiltH: ShaderPass;
  private tiltV: ShaderPass;
  private bloom: UnrealBloomPass;
  private finish: ShaderPass;
  private night = 0;

  constructor(
    private renderer: THREE.WebGLRenderer,
    scene: THREE.Scene,
    camera: THREE.Camera,
  ) {
    const rt = new THREE.WebGLRenderTarget(1, 1, { type: THREE.HalfFloatType, samples: 4 });
    this.composer = new EffectComposer(renderer, rt);
    this.composer.addPass(new RenderPass(scene, camera));
    this.tiltH = new ShaderPass(TiltShift);
    this.tiltV = new ShaderPass(TiltShift);
    this.composer.addPass(this.tiltH);
    this.composer.addPass(this.tiltV);
    this.bloom = new UnrealBloomPass(new THREE.Vector2(256, 256), 0.35, 0.55, 0.92);
    this.composer.addPass(this.bloom);
    this.composer.addPass(new OutputPass());
    this.finish = new ShaderPass(Finish);
    this.composer.addPass(this.finish);
  }

  setTier(t: Tier) {
    this.tier = t;
    this.apply();
  }

  setNight(n: number) {
    this.night = n;
    this.apply();
  }

  private apply() {
    const hi = this.tier === 'high';
    this.tiltH.enabled = this.tiltV.enabled = hi;
    // bloom is subtle by day (sun glints on water/steel) and carries the lamps at night
    this.bloom.enabled = hi || (this.tier === 'medium' && this.night > 0.3);
    this.bloom.strength = THREE.MathUtils.lerp(0.15, 0.55, this.night);
    this.bloom.threshold = THREE.MathUtils.lerp(0.95, 0.62, this.night);
    this.bloom.radius = 0.5;
  }

  setSize(w: number, h: number, dpr: number) {
    this.composer.setPixelRatio(dpr);
    this.composer.setSize(w, h);
    const pw = w * dpr;
    const ph = h * dpr;
    this.tiltH.uniforms.uStep.value.set(1 / pw, 0);
    this.tiltV.uniforms.uStep.value.set(0, 1 / ph);
    // tilt-shift strength scales with resolution so it looks the same at any DPR
    const amt = 1.5 * Math.max(1, dpr * 0.8);
    this.tiltH.uniforms.uAmount.value = amt;
    this.tiltV.uniforms.uAmount.value = amt;
    this.finish.uniforms.uTexel.value.set(1 / pw, 1 / ph);
    this.bloom.resolution.set(Math.max(1, pw / 2), Math.max(1, ph / 2));
  }

  render(dt: number, time: number) {
    if (this.tier === 'low') {
      this.renderer.render(this.composer.passes[0] instanceof RenderPass ? (this.composer.passes[0] as RenderPass).scene : new THREE.Scene(), (this.composer.passes[0] as RenderPass).camera);
      return;
    }
    this.finish.uniforms.uTime.value = time % 100;
    this.composer.render(dt);
  }
}
