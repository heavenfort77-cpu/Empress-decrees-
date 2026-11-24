// Apex Tiger Demon and cubs: material states and the school-colour variant rule (W4, 25 Nov; art tool, not shipped yet).
// Same mesh and UVs in every state; only materials change (GDD: the winner's colour is a material tint plus emblem, no new model).
//   awake   : apexBronze = bronze_trim.png (fresh brass-gold), apexCrack and apexOrgan glow water-blue (SUITS.md: the cracks glow
//             black and water-blue), apexInlay polished gold.
//   dormant : apexBronze = apex_patina.png (same layout, patina painted over in klad), crack and organ lines dull, no glow.
//   school  : index into CONFIG.SCHOOLS; bronze tinted toward COL.schools[i] (TINT_AWAKE / TINT_DORMANT), crack lines and organs take
//             the school colour (glowing awake, unlit inlay asleep). Emblem decal not built (needs the emblem art).
// Glow colour WATER is deliberately bluer and darker than the reserved hazard hue #3FE6F0 and the Howler tell 0x40e0ff.
// CONFIG -----------------------------------------------------------------------------------------------------------------
// School colours, index.html COL.schools (CONFIG.SCHOOLS order: ru dao fa mo yinyang za ming zongheng nong).
export const SCHOOLS = [0xb05a2a, 0xd5a03a, 0x6a6a6a, 0x8a2a3a, 0x3a3a3a, 0xe8e8f0, 0xc060a0, 0x40c0c0, 0x9a6ad5];
// Awake crack and organ glow (water-blue) and its intensities.
export const WATER = 0x3a8fd0, CRACK_GLOW = 1.4, ORGAN_GLOW = 0.9;
// Bronze tint strength toward the school colour (0 = none), awake and dormant.
export const TINT_AWAKE = 0.4, TINT_DORMANT = 0.25;
// Bronze surface (study: metalness 0.4, roughness 0.6; patina is matte).
export const BRONZE = { metalness: 0.4, roughness: 0.6 }, PATINA = { metalness: 0.15, roughness: 0.85 };

// lift a colour so its brightest channel is 1 (a black school still glows, as grey-white)
function lift(THREE, hex) { const c = new THREE.Color(hex); const m = Math.max(c.r, c.g, c.b, 1e-3); return c.multiplyScalar(1 / m); }

// tex(path) must return a THREE.Texture (sRGB, flipY false for glTF UVs). Returns { name: material }.
export function apexMaterials(THREE, tex, state = 'awake', school = null) {
  const awake = state !== 'dormant', sc = school === null || school === undefined || school < 0 ? null : SCHOOLS[school];
  const tint = sc === null ? new THREE.Color(1, 1, 1) : new THREE.Color(1, 1, 1).lerp(new THREE.Color(sc), awake ? TINT_AWAKE : TINT_DORMANT);
  const glow = sc === null ? new THREE.Color(WATER) : lift(THREE, sc);
  const bronze = new THREE.MeshStandardMaterial({ map: tex(awake ? '../../assets/tex/bronze_trim.png' : '../../assets/tex/apex_patina.png'), color: tint, ...(awake ? BRONZE : PATINA) });
  const crack = awake
    ? new THREE.MeshStandardMaterial({ color: 0x1d3140, emissive: glow, emissiveIntensity: CRACK_GLOW, metalness: 0.3, roughness: 0.5, side: THREE.DoubleSide })
    : new THREE.MeshStandardMaterial({ color: sc === null ? 0x6b5a2a : new THREE.Color(sc).multiplyScalar(0.8), metalness: 0.3, roughness: 0.7, side: THREE.DoubleSide });
  const organ = awake
    ? new THREE.MeshStandardMaterial({ color: 0x10181f, emissive: glow, emissiveIntensity: ORGAN_GLOW, metalness: 0.2, roughness: 0.3 })
    : new THREE.MeshStandardMaterial({ color: 0x2a2f2a, metalness: 0.2, roughness: 0.8 });
  const inlay = awake ? new THREE.MeshStandardMaterial({ color: 0xe2b84a, metalness: 0.6, roughness: 0.35 }) : new THREE.MeshStandardMaterial({ color: 0x8a7a48, metalness: 0.3, roughness: 0.7 });
  const dark = new THREE.MeshStandardMaterial({ color: 0x1a120c, roughness: 0.9 });
  return { apexBronze: bronze, apexCrack: crack, apexOrgan: organ, apexInlay: inlay, apexDark: dark };
}
