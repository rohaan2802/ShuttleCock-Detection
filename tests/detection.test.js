import test from 'node:test';
import assert from 'node:assert/strict';
import {letterbox,rgbTensor,decode,iou} from '../docs/detection.js';

test('letterboxing and decoding preserve landscape camera coordinates',()=>{
  const t=letterbox(640,480);
  assert.equal(t.top,40);assert.equal(t.left,0);
  const boxes=decode(new Float32Array([160,160,100,50,.9]),[1,5,1],t);
  assert.equal(boxes.length,1);
  assert.deepEqual([boxes[0].x1,boxes[0].y1,boxes[0].x2,boxes[0].y2],[220,190,420,290]);
});
test('portrait coordinates are clipped and overlapping predictions suppressed',()=>{
  const t=letterbox(480,640);
  const raw=new Float32Array([160,161,20,160,161,20,100,100,80,100,100,80,.9,.8,.1]);
  const boxes=decode(raw,[1,5,3],t,.35);
  assert.equal(boxes.length,1);assert.equal(boxes[0].x1,140);
  assert.equal(decode(raw,[1,5,3],t,.95).length,0);
});
test('RGB channels are planar and normalized',()=>{
  assert.deepEqual(Array.from(rgbTensor(new Uint8ClampedArray([255,0,255,255]),1)),[1,0,1]);
});
test('empty and malformed detections are handled safely',()=>{
  assert.deepEqual(decode(new Float32Array(5),[1,5,1],letterbox(640,480)),[]);
  assert.throws(()=>decode(new Float32Array(6),[1,6,1],letterbox(640,480)));
  assert.equal(iou({x1:0,y1:0,x2:10,y2:10},{x1:20,y1:20,x2:30,y2:30}),0);
});
