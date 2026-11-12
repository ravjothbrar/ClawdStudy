// Shared materials with a tiny shader patch for the "blocks drop into place" reveal.
// Every vertex carries `_drop` (0..1, bottom blocks first) from Blender; uReveal
// sweeps 0 -> 1 and each block falls from above with a little overshoot.
import * as THREE from 'three';

export interface RevealUniforms {
  uReveal: { value: number };
}

const PATCH_KEY = 'clawd-reveal-v1';

function patch(m: THREE.Material, u: RevealUniforms) {
  m.onBeforeCompile = (shader) => {
    shader.uniforms.uReveal = u.uReveal;
    shader.vertexShader = shader.vertexShader
      .replace(
        '#include <common>',
        `#include <common>
attribute float _drop;
uniform float uReveal;
float clawdBack(float t){ float c1 = 1.70158; float c3 = c1 + 1.0; return 1.0 + c3*pow(t-1.0,3.0) + c1*pow(t-1.0,2.0); }`,
      )
      .replace(
        '#include <begin_vertex>',
        `#include <begin_vertex>
float clawdT = clamp((uReveal * 1.45 - _drop) / 0.45, 0.0, 1.0);
float clawdS = length(modelMatrix[1].xyz); // meshes are quantized, so undo node scale
transformed.y += (1.0 - clawdBack(clawdT)) * 7.0 / clawdS;
if (clawdT <= 0.0) transformed.y += 10000.0 / clawdS;`,
      );
  };
  m.customProgramCacheKey = () => PATCH_KEY;
}

export function makeRegionMaterials(revealed: boolean) {
  const u: RevealUniforms = { uReveal: { value: revealed ? 1 : 0 } };
  const solid = new THREE.MeshLambertMaterial({ vertexColors: true });
  const glow = new THREE.MeshBasicMaterial({ vertexColors: true });
  patch(solid, u);
  patch(glow, u);
  return { u, solid, glow };
}

export const clawdMaterial = new THREE.MeshLambertMaterial({ vertexColors: true });
