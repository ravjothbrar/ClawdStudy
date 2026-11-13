// Shared PBR materials with two small shader patches:
//  * reveal: every vertex carries `_drop` (0..1, bottom blocks first) from Blender; uReveal
//    sweeps 0 -> 1 and each block falls from above with a little overshoot.
//  * `_pbr`: per-vertex (roughness, metalness) baked in Blender, so one material (one draw
//    call) can hold matte grass, glossy water and brushed steel side by side.
import * as THREE from 'three';

export interface RevealUniforms {
  uReveal: { value: number };
}

const PATCH_KEY = 'clawd-pbr-v2';

const DROP_PARS = /* glsl */ `
attribute float _drop;
uniform float uReveal;
float clawdBack(float t){ float c1 = 1.70158; float c3 = c1 + 1.0; return 1.0 + c3*pow(t-1.0,3.0) + c1*pow(t-1.0,2.0); }`;

const DROP_VERTEX = /* glsl */ `
float clawdT = clamp((uReveal * 1.45 - _drop) / 0.45, 0.0, 1.0);
float clawdS = length(modelMatrix[1].xyz); // meshes are quantized, so undo node scale
transformed.y += (1.0 - clawdBack(clawdT)) * 7.0 / clawdS;
if (clawdT <= 0.0) transformed.y += 10000.0 / clawdS;`;

function patchStandard(m: THREE.MeshStandardMaterial, u: RevealUniforms | null) {
  m.onBeforeCompile = (shader) => {
    if (u) shader.uniforms.uReveal = u.uReveal;
    shader.vertexShader = shader.vertexShader
      .replace(
        '#include <common>',
        `#include <common>
attribute vec2 _pbr;
varying vec2 vClawdPbr;
${u ? DROP_PARS : ''}`,
      )
      .replace(
        '#include <begin_vertex>',
        `#include <begin_vertex>
vClawdPbr = _pbr;
${u ? DROP_VERTEX : ''}`,
      );
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', `#include <common>\nvarying vec2 vClawdPbr;`)
      .replace(
        '#include <roughnessmap_fragment>',
        // meshes without _pbr read (0,0): fall back to a satin default
        `float roughnessFactor = roughness * (vClawdPbr.x > 0.001 ? vClawdPbr.x : 0.8);`,
      )
      .replace('#include <metalnessmap_fragment>', `float metalnessFactor = metalness * vClawdPbr.y;`);
  };
  m.customProgramCacheKey = () => PATCH_KEY + (u ? '-r' : '');
}

function patchBasic(m: THREE.MeshBasicMaterial, u: RevealUniforms) {
  m.onBeforeCompile = (shader) => {
    shader.uniforms.uReveal = u.uReveal;
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', `#include <common>\n${DROP_PARS}`)
      .replace('#include <begin_vertex>', `#include <begin_vertex>\n${DROP_VERTEX}`);
  };
  m.customProgramCacheKey = () => PATCH_KEY + '-glow';
}

export interface RegionMaterials {
  u: RevealUniforms;
  /** static, lightmapped geometry */
  baked: THREE.MeshStandardMaterial;
  /** moving parts (no lightmap, lit by sun + environment) */
  solid: THREE.MeshStandardMaterial;
  /** windows, lamps, beacons: emissive, bloom at night */
  glow: THREE.MeshBasicMaterial;
}

export function makeRegionMaterials(revealed: boolean): RegionMaterials {
  const u: RevealUniforms = { uReveal: { value: revealed ? 1 : 0 } };
  const baked = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 1, metalness: 1, envMapIntensity: 0.45 });
  const solid = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 1, metalness: 1, envMapIntensity: 1.0 });
  const glow = new THREE.MeshBasicMaterial({ vertexColors: true });
  patchStandard(baked, u);
  patchStandard(solid, u);
  patchBasic(glow, u);
  return { u, baked, solid, glow };
}

/** Clone a glow material that keeps the reveal patch (for pulsing / night-only parts). */
export function cloneGlow(glow: THREE.MeshBasicMaterial) {
  const m = glow.clone();
  m.onBeforeCompile = glow.onBeforeCompile;
  m.customProgramCacheKey = glow.customProgramCacheKey;
  return m;
}

/** Clawd: satin clay body, glossy eye slots (per-vertex roughness from Blender). */
export const clawdMaterial = new THREE.MeshStandardMaterial({
  vertexColors: true,
  roughness: 1,
  metalness: 1,
  envMapIntensity: 1.15,
});
patchStandard(clawdMaterial, null);
