# Credits

- three.js r171 (lib/), MIT licence, three.js authors. https://github.com/mrdoob/three.js
- Palace textures (assets/tex/*.png) painted with klad (https://github.com/klad-app/klad). The drawings are ours; only the exported PNGs ship, no klad code. Sources: art/src/*.klad, generator art/tools/palace_tex.py.
- All game code, systems, art and sound: Empress Decrees team.
- three.js GLTFLoader and BufferGeometryUtils r171 (MIT, mrdoob and contributors), used by the art review viewer art/viewer/ (not shipped in the game yet).
- lib/jsm/ (batch 17a, vendored unchanged from three.js r171 examples/jsm): GLTFLoader, KTX2Loader, BufferGeometryUtils, SkeletonUtils, WorkerPool, ColorSpaces (MIT, three.js authors);
  meshopt_decoder (MIT, Arseny Kapoulkine, https://github.com/zeux/meshoptimizer); ktx-parse and zstddec (MIT, Don McCurdy); basis_transcoder.js/.wasm
  (Apache-2.0, Binomial LLC, https://github.com/BinomialLLC/basis_universal).
- Asset encoders used at build time only (not shipped): KTX-Software toktx (Apache-2.0, Khronos Group), glTF-Transform (MIT, Don McCurdy).
