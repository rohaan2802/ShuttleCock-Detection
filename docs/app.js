import {letterbox,rgbTensor,decode} from './detection.js';
const $=id=>document.getElementById(id), video=$('video'), canvas=$('view'), ctx=canvas.getContext('2d');
const input=document.createElement('canvas'); input.width=input.height=320;
const ic=input.getContext('2d',{willReadFrequently:true});
const frame=document.createElement('canvas'), fc=frame.getContext('2d');
let sessionPromise, stream, running=false, generation=0, pendingInference=Promise.resolve();
const status=text=>{$('status').textContent=text;};
function session() {
  if (!sessionPromise) sessionPromise=(async()=>{
    if (!window.ort) throw new Error('Detector files did not load. Refresh the page and try again.');
    ort.env.wasm.wasmPaths=new URL('./vendor/',location.href).href;
    ort.env.wasm.numThreads=1;
    return ort.InferenceSession.create(new URL('./models/shuttle.onnx',location.href).href,{executionProviders:['wasm']});
  })().catch(error=>{sessionPromise=null;throw error;});
  return sessionPromise;
}
function stop(message='Camera stopped.') {
  generation++; running=false;
  stream?.getTracks().forEach(track=>track.stop());stream=null;video.srcObject=null;
  $('start').disabled=false;$('stop').disabled=true;$('camera').disabled=false;
  canvas.hidden=true;$('empty').hidden=false;$('indicator').classList.remove('live');
  $('resolution').textContent='OFFLINE';$('count').textContent='—';$('fps').textContent='— FPS';
  $('coordinates').textContent='X — / Y —';$('match').textContent='Highest-confidence match';status(message);
}
async function loop(token, model) {
  if(!running || token!==generation)return;
  try {
    if(video.readyState<2){requestAnimationFrame(()=>loop(token,model));return;}
    const started=performance.now(),w=video.videoWidth,h=video.videoHeight,t=letterbox(w,h);
    if(frame.width!==w || frame.height!==h){frame.width=canvas.width=w;frame.height=canvas.height=h;}
    fc.drawImage(video,0,0,w,h);
    ic.fillStyle='rgb(114,114,114)';ic.fillRect(0,0,320,320);ic.drawImage(frame,0,0,w,h,t.left,t.top,t.w,t.h);
    const tensor=new ort.Tensor('float32',rgbTensor(ic.getImageData(0,0,320,320).data),[1,3,320,320]);
    let output;
    try { pendingInference=model.run({[model.inputNames[0]]:tensor});output=await pendingInference; } finally {tensor.dispose();}
    let boxes;
    try {const raw=output[model.outputNames[0]];boxes=decode(raw.data,raw.dims,t,Number($('confidence').value)/100);}
    finally {Object.values(output).forEach(value=>value.dispose());}
    if(!running || token!==generation)return;
    ctx.drawImage(frame,0,0);ctx.strokeStyle='#d2f59a';ctx.lineWidth=Math.max(2,w/320);ctx.font=`600 ${Math.max(14,w/45)}px sans-serif`;
    for(const b of boxes){
      ctx.strokeRect(b.x1,b.y1,b.x2-b.x1,b.y2-b.y1);
      const label=`Shuttle ${Math.round(b.score*100)}%`,size=Math.max(14,w/45),tw=ctx.measureText(label).width+12,ly=Math.max(size+10,b.y1);
      ctx.fillStyle='#d2f59a';ctx.fillRect(b.x1,ly-size-10,tw,size+10);ctx.fillStyle='#10251f';ctx.fillText(label,b.x1+6,ly-5);
      ctx.fillStyle='#d2f59a';ctx.beginPath();ctx.arc((b.x1+b.x2)/2,(b.y1+b.y2)/2,4,0,Math.PI*2);ctx.fill();
    }
    $('count').textContent=String(boxes.length);$('fps').textContent=`${(1000/(performance.now()-started)).toFixed(1)} FPS`;
    const best=boxes[0];$('coordinates').textContent=best?`X ${Math.round((best.x1+best.x2)/2)} / Y ${Math.round((best.y1+best.y2)/2)}`:'X — / Y —';
    $('match').textContent=best?`${Math.round(best.score*100)}% confidence · highest match`:'Waiting for a shuttlecock';
    status(best?'Shuttlecock detected.':'No shuttlecock detected. Camera is still running.');
    requestAnimationFrame(()=>loop(token,model));
  } catch(error){if(token===generation){console.error(error);stop('Detection failed. Please restart the camera.');}}
}
$('start').addEventListener('click',async()=>{
  const token=++generation;$('start').disabled=true;$('stop').disabled=false;$('camera').disabled=true;
  try {
    if(!navigator.mediaDevices?.getUserMedia)throw new Error('Camera requires HTTPS or localhost in a supported browser.');
    status('Allow camera access to continue…');
    const acquired=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:$('camera').value},width:{ideal:640},height:{ideal:480}},audio:false});
    if(token!==generation){acquired.getTracks().forEach(t=>t.stop());return;}
    stream=acquired;video.srcObject=stream;await video.play();
    stream.getVideoTracks()[0].addEventListener('ended',()=>{if(token===generation)stop('Camera disconnected. Please restart.');});
    status('Loading detector for the first frame…');const model=await session();
    await pendingInference.catch(()=>{});
    if(token!==generation)return;
    running=true;canvas.hidden=false;$('empty').hidden=true;$('indicator').classList.add('live');$('resolution').textContent=`${video.videoWidth} × ${video.videoHeight}`;
    loop(token,model);
  } catch(error){if(token===generation){console.error(error);stop(error.name==='NotAllowedError'?'Camera access denied. Allow it in browser settings, then retry.':error.name==='NotFoundError'?'No camera found. Connect a camera and try again.':error.name==='NotReadableError'?'Camera is busy. Close other camera apps and retry.':error.message);}}
});
$('stop').addEventListener('click',()=>stop());
$('confidence').addEventListener('input',()=>{$('confidence-value').value=`${$('confidence').value}%`;});
window.addEventListener('pagehide',()=>stop());
document.addEventListener('visibilitychange',()=>{if(document.hidden && (running || stream))stop('Camera paused while this tab is hidden. Restart when ready.');});
