// YOLOv8 raw output: [1, 4 + class_count, candidates], RGB / 255 input.
export function letterbox(width, height, size = 320) {
  const scale = Math.min(size / width, size / height);
  const w = Math.round(width * scale), h = Math.round(height * scale);
  return { width, height, size, scale, w, h, left: Math.max(0, Math.round((size - w) / 2 - 0.1)), top: Math.max(0, Math.round((size - h) / 2 - 0.1)) };
}
export function rgbTensor(rgba, size = 320) {
  const pixels = size * size, data = new Float32Array(3 * pixels);
  for (let i = 0; i < pixels; i++) for (let c = 0; c < 3; c++) data[c * pixels + i] = rgba[i * 4 + c] / 255;
  return data;
}
export function iou(a, b) {
  const intersection = Math.max(0, Math.min(a.x2,b.x2)-Math.max(a.x1,b.x1)) * Math.max(0,Math.min(a.y2,b.y2)-Math.max(a.y1,b.y1));
  return intersection / Math.max(1e-9, (a.x2-a.x1)*(a.y2-a.y1)+(b.x2-b.x1)*(b.y2-b.y1)-intersection);
}
export function decode(data, dims, transform, confidence = .35, overlap = .5) {
  if (dims.length !== 3 || dims[0] !== 1 || dims[1] !== 5) throw new Error('Expected a single-class YOLOv8 detection model.');
  const n = dims[2], candidates = [], {left,top,scale,width,height} = transform;
  const clamp = (x, max) => Math.max(0,Math.min(max,x));
  for (let i=0; i<n; i++) {
    const score=data[4*n+i];
    if (!Number.isFinite(score) || score<confidence) continue;
    const x=data[i], y=data[n+i], w=data[2*n+i], h=data[3*n+i];
    const box={score,x1:clamp((x-w/2-left)/scale,width),y1:clamp((y-h/2-top)/scale,height),x2:clamp((x+w/2-left)/scale,width),y2:clamp((y+h/2-top)/scale,height)};
    if (Object.values(box).every(Number.isFinite) && box.x2>box.x1 && box.y2>box.y1) candidates.push(box);
  }
  candidates.sort((a,b)=>b.score-a.score);
  const selected=[];
  for (const box of candidates) {
    if (selected.every(other=>iou(box,other)<=overlap)) selected.push(box);
    if (selected.length>=100) break;
  }
  return selected;
}
