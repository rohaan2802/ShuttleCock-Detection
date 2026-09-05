import {mkdir,copyFile} from 'node:fs/promises';
await mkdir('docs/vendor',{recursive:true});
for(const file of ['ort-wasm-simd-threaded.mjs','ort-wasm-simd-threaded.wasm']) {
  await copyFile(`node_modules/onnxruntime-web/dist/${file}`,`docs/vendor/${file}`);
}
await copyFile('node_modules/onnxruntime-web/dist/ort.wasm.min.js','docs/vendor/ort.min.js');
console.log('Pinned ONNX Runtime Web 1.22.0 copied to docs/vendor.');
