// Runs the shipped browser WASM backend against the Python reference output.
import * as ort from 'onnxruntime-web';
import {readFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
import {decode,letterbox} from '../docs/detection.js';
ort.env.wasm.numThreads=1;
const floats=async path=>{const b=await readFile(path);return new Float32Array(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength));};
const data=await floats('.test-output/input.f32'), expected=await floats('.test-output/expected.f32');
const session=await ort.InferenceSession.create(await readFile('docs/models/shuttle.onnx'),{executionProviders:['wasm']});
const result=await session.run({images:new ort.Tensor('float32',data,[1,3,320,320])});
const output=result[session.outputNames[0]];
assert.deepEqual(output.dims,[1,5,2100]);
let maxError=0;
for(let i=0;i<expected.length;i++){
  const error=Math.abs(expected[i]-output.data[i]);maxError=Math.max(maxError,error);
  assert.ok(error<.003+Math.abs(expected[i])*.001,`WASM mismatch at ${i}: ${error}`);
}
const boxes=decode(output.data,output.dims,letterbox(320,320));
assert.ok(boxes.length>0,'The repository sample should produce a shuttle detection');
console.log(JSON.stringify({backend:'wasm',shape:output.dims,maxError,detections:boxes},null,2));
await session.release();
