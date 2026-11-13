// A tiny procedural sky, prefiltered into a PMREM environment for reflections and
// soft image-based light. Regenerated only when the time of day moves noticeably.
import * as THREE from 'three';

export class SkyEnv {
  private pmrem: THREE.PMREMGenerator;
  private scene = new THREE.Scene();
  private mat: THREE.ShaderMaterial;
  private rt: THREE.WebGLRenderTarget | null = null;
  private lastNight = -1;

  constructor(renderer: THREE.WebGLRenderer) {
    this.pmrem = new THREE.PMREMGenerator(renderer);
    this.mat = new THREE.ShaderMaterial({
      side: THREE.BackSide,
      depthWrite: false,
      uniforms: {
        uZenith: { value: new THREE.Color() },
        uHorizon: { value: new THREE.Color() },
        uGround: { value: new THREE.Color() },
        uSunDir: { value: new THREE.Vector3(0.5, 0.7, 0.5).normalize() },
        uSunCol: { value: new THREE.Color() },
      },
      vertexShader: /* glsl */ `
        varying vec3 vDir;
        void main() {
          vDir = normalize(position);
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }`,
      fragmentShader: /* glsl */ `
        uniform vec3 uZenith, uHorizon, uGround, uSunDir, uSunCol;
        varying vec3 vDir;
        void main() {
          vec3 d = normalize(vDir);
          float up = d.y;
          vec3 sky = mix(uHorizon, uZenith, smoothstep(0.0, 0.65, up));
          vec3 col = up >= 0.0 ? sky : mix(uHorizon * 0.9, uGround, smoothstep(0.0, -0.35, up));
          float s = max(dot(d, uSunDir), 0.0);
          col += uSunCol * (pow(s, 600.0) * 40.0 + pow(s, 12.0) * 0.6);
          gl_FragColor = vec4(col, 1.0);
        }`,
    });
    this.scene.add(new THREE.Mesh(new THREE.SphereGeometry(10, 48, 24), this.mat));
  }

  /** Returns a new env texture when it changed, otherwise null. */
  update(night: number, sunDir: THREE.Vector3): THREE.Texture | null {
    if (this.lastNight >= 0 && Math.abs(night - this.lastNight) < 0.08) return null;
    this.lastNight = night;
    const u = this.mat.uniforms;
    const day = { z: new THREE.Color(0x7fa3d6), h: new THREE.Color(0xf4e6d0), g: new THREE.Color(0x8a7b68) };
    const dusk = { z: new THREE.Color(0x6c78b8), h: new THREE.Color(0xf2b48c), g: new THREE.Color(0x5e4c48) };
    const nite = { z: new THREE.Color(0x0e1530), h: new THREE.Color(0x2b3352), g: new THREE.Color(0x101218) };
    const pick = (k: 'z' | 'h' | 'g') =>
      night < 0.5 ? day[k].clone().lerp(dusk[k], night * 2) : dusk[k].clone().lerp(nite[k], (night - 0.5) * 2);
    (u.uZenith.value as THREE.Color).copy(pick('z'));
    (u.uHorizon.value as THREE.Color).copy(pick('h'));
    (u.uGround.value as THREE.Color).copy(pick('g'));
    (u.uSunDir.value as THREE.Vector3).copy(sunDir).normalize();
    (u.uSunCol.value as THREE.Color).set(night > 0.5 ? 0x8fa6ff : 0xfff0d8).multiplyScalar(night > 0.5 ? 0.25 : 1);
    const prev = this.rt;
    this.rt = this.pmrem.fromScene(this.scene, 0, 0.1, 50);
    prev?.dispose();
    return this.rt.texture;
  }
}
