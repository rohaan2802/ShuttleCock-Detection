import {letterbox,rgbTensor,decode} from './detection.js';
const $=id=>document.getElementById(id), video=$('video'), canvas=$('view'), ctx=canvas.getContext('2d');
const input=document.createElement('canvas'); input.width=input.height=320;
const ic=input.getContext('2d',{willReadFrequently:true});
const frame=document.createElement('canvas'), fc=frame.getContext('2d');
const displayedFrame=document.createElement('canvas'), dc=displayedFrame.getContext('2d');
let sessionPromise, stream, running=false, generation=0, pendingInference=Promise.resolve();
let paused=false, frames=0, startedAt=0, timer, lastBoxes=[], smoothedFps=0;
const status=text=>{if($('status').textContent!==text)$('status').textContent=text;};
function setState(state) {
  $('camera-panel').dataset.state=state;
  $('mode-badge').textContent={idle:'STANDBY',loading:'CONNECTING',live:'LIVE',paused:'PAUSED'}[state];
}
function updateTime() {
  const seconds=Math.floor((performance.now()-startedAt)/1000);
  $('elapsed').textContent=`${String(Math.floor(seconds/60)).padStart(2,'0')}:${String(seconds%60).padStart(2,'0')}`;
}
function savePreferences() {
  try {localStorage.setItem('shuttlebot-view',JSON.stringify({confidence:Number($('confidence').value),grid:$('grid').checked,mirror:$('mirror').checked}));} catch {}
}
function syncPreferences() {
  $('confidence-value').value=`${$('confidence').value}%`;
  $('confidence').style.setProperty('--progress',`${(Number($('confidence').value)-10)/80*100}%`);
  $('grid-overlay').hidden=!$('grid').checked || !running;
}
try {
  const saved=JSON.parse(localStorage.getItem('shuttlebot-view')||'{}');
  if(Number.isFinite(saved.confidence))$('confidence').value=String(Math.max(10,Math.min(90,saved.confidence)));
  $('grid').checked=saved.grid===true;$('mirror').checked=saved.mirror===true;
} catch {}
syncPreferences();
function render(boxes,w,h) {
  ctx.save();
  if($('mirror').checked){ctx.translate(w,0);ctx.scale(-1,1);}
  ctx.drawImage(displayedFrame,0,0);ctx.restore();
  ctx.strokeStyle='#5eead4';ctx.lineWidth=Math.max(2,w/320);ctx.font=`600 ${Math.max(14,w/45)}px sans-serif`;
  for(const b of boxes){
    const x=$('mirror').checked?w-b.x2:b.x1,bw=b.x2-b.x1;
    ctx.strokeRect(x,b.y1,bw,b.y2-b.y1);
    const label=`Shuttle ${Math.round(b.score*100)}%`,size=Math.max(14,w/45),tw=ctx.measureText(label).width+12,ly=Math.max(size+10,b.y1),lx=Math.min(x,w-tw);
    ctx.fillStyle='#5eead4';ctx.fillRect(lx,ly-size-10,tw,size+10);ctx.fillStyle='#09221f';ctx.fillText(label,lx+6,ly-5);
    ctx.fillStyle='#5eead4';ctx.beginPath();ctx.arc(x+bw/2,(b.y1+b.y2)/2,4,0,Math.PI*2);ctx.fill();
  }
}
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
  if(startedAt){updateTime();startedAt=0;}
  clearInterval(timer);generation++; running=false;paused=false;lastBoxes=[];
  stream?.getTracks().forEach(track=>track.stop());stream=null;video.srcObject=null;
  $('start').disabled=false;$('stop').disabled=true;$('camera').disabled=false;
  $('pause').disabled=true;$('pause').textContent='Pause detection';$('pause').setAttribute('aria-pressed','false');
  $('snapshot').disabled=true;
  $('paused-overlay').hidden=true;$('grid-overlay').hidden=true;
  $('target-dot').hidden=true;$('confidence-bar').style.width='0%';$('target-state').textContent='NO TARGET';
  $('session-note').textContent=frames?'Session ended':'Waiting to start';setState('idle');
  canvas.hidden=true;$('empty').hidden=false;$('indicator').classList.remove('live');
  $('resolution').textContent='CAMERA OFF';$('count').textContent='—';$('fps').textContent='— FPS';
  $('coordinates').textContent='X — / Y —';$('match').textContent='Highest-confidence match';status(message);
}
async function loop(token, model) {
  if(!running || token!==generation)return;
  if(paused){requestAnimationFrame(()=>loop(token,model));return;}
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
    if(paused){requestAnimationFrame(()=>loop(token,model));return;}
    if(displayedFrame.width!==w || displayedFrame.height!==h){displayedFrame.width=w;displayedFrame.height=h;}
    dc.drawImage(frame,0,0);lastBoxes=boxes;render(boxes,w,h);
    frames++;$('frames').textContent=frames.toLocaleString();
    const fps=1000/(performance.now()-started);smoothedFps=smoothedFps?smoothedFps*.8+fps*.2:fps;
    $('count').textContent=String(boxes.length);$('fps').textContent=`${smoothedFps.toFixed(1)} FPS`;
    const best=boxes[0];$('coordinates').textContent=best?`X ${Math.round((best.x1+best.x2)/2)} / Y ${Math.round((best.y1+best.y2)/2)}`:'X — / Y —';
    $('match').textContent=best?`${Math.round(best.score*100)}% confidence · highest match`:'Waiting for a shuttlecock';
    $('target-state').textContent=best?'TRACKING':'NO TARGET';$('confidence-bar').style.width=best?`${best.score*100}%`:'0%';
    $('target-dot').hidden=!best;
    if(best){$('target-dot').style.left=`${(best.x1+best.x2)/2/w*100}%`;$('target-dot').style.top=`${(best.y1+best.y2)/2/h*100}%`;}
    status(best?'Shuttlecock detected.':'No shuttlecock detected. Camera is still running.');
    requestAnimationFrame(()=>loop(token,model));
  } catch(error){if(token===generation){console.error(error);stop('Detection failed. Please restart the camera.');}}
}
$('start').addEventListener('click',async()=>{
  const token=++generation;$('start').disabled=true;$('stop').disabled=false;$('camera').disabled=true;
  setState('loading');
  try {
    if(!navigator.mediaDevices?.getUserMedia)throw new Error('Camera requires HTTPS or localhost in a supported browser.');
    status('Allow camera access to continue…');
    const choice=$('camera').value,source=choice.startsWith('device:')?{deviceId:{exact:choice.slice(7)}}:{facingMode:{ideal:choice}};
    const acquired=await navigator.mediaDevices.getUserMedia({video:{...source,width:{ideal:640},height:{ideal:480}},audio:false});
    if(token!==generation){acquired.getTracks().forEach(t=>t.stop());return;}
    stream=acquired;video.srcObject=stream;await video.play();
    // Camera names become available only after permission is granted.
    navigator.mediaDevices.enumerateDevices().then(devices=>{
      if(token!==generation)return;
      $('camera').querySelectorAll('option[data-device]').forEach(option=>option.remove());
      devices.filter(device=>device.kind==='videoinput' && device.deviceId).forEach((device,index)=>{
        const option=new Option(device.label||`Camera ${index+1}`,`device:${device.deviceId}`);option.dataset.device='true';$('camera').add(option);
      });
      const deviceId=acquired.getVideoTracks()[0].getSettings().deviceId;
      if(deviceId && [...$('camera').options].some(option=>option.value===`device:${deviceId}`))$('camera').value=`device:${deviceId}`;
    }).catch(()=>{});
    stream.getVideoTracks()[0].addEventListener('ended',()=>{if(token===generation)stop('Camera disconnected. Please restart.');});
    status('Loading detector for the first frame…');const model=await session();
    await pendingInference.catch(()=>{});
    if(token!==generation)return;
    running=true;canvas.hidden=false;$('empty').hidden=true;$('indicator').classList.add('live');$('resolution').textContent=`${video.videoWidth} × ${video.videoHeight}`;
    paused=false;frames=0;smoothedFps=0;lastBoxes=[];startedAt=performance.now();$('frames').textContent='0';$('elapsed').textContent='00:00';
    timer=setInterval(updateTime,1000);$('session-note').textContent='Camera active';$('pause').disabled=false;setState('live');syncPreferences();
    $('snapshot').disabled=false;
    loop(token,model);
  } catch(error){if(token===generation){console.error(error);stop(error.name==='NotAllowedError'?'Camera access denied. Allow it in browser settings, then retry.':error.name==='NotFoundError'?'No camera found. Connect a camera and try again.':error.name==='NotReadableError'?'Camera is busy. Close other camera apps and retry.':error.message);}}
});
$('stop').addEventListener('click',()=>stop());
$('snapshot').addEventListener('click',()=>{
  if(!running || !displayedFrame.width)return;
  const link=document.createElement('a');link.download=`shuttlebot-${new Date().toISOString().replace(/[:.]/g,'-')}.png`;
  link.href=canvas.toDataURL('image/png');link.click();status('Snapshot saved to your downloads.');
});
$('reset').addEventListener('click',()=>{
  stop('Session reset. Ready when you are.');frames=0;smoothedFps=0;
  $('frames').textContent='0';$('elapsed').textContent='00:00';$('session-note').textContent='Waiting to start';
});
$('pause').addEventListener('click',()=>{
  if(!running)return;paused=!paused;
  $('pause').textContent=paused?'Resume detection':'Pause detection';$('pause').setAttribute('aria-pressed',String(paused));
  $('paused-overlay').hidden=!paused;setState(paused?'paused':'live');
  $('session-note').textContent=paused?'Detection paused · camera on':'Camera active';
  if(paused){$('fps').textContent='— FPS';$('target-state').textContent='PAUSED';status('Detection paused. Camera remains on.');}
  else status('Resuming detection…');
});
for(const id of ['confidence','grid','mirror'])$(id).addEventListener(id==='confidence'?'input':'change',()=>{
  syncPreferences();savePreferences();
  if(id==='mirror' && running && frames)render(lastBoxes,displayedFrame.width,displayedFrame.height);
});
function syncFullscreen() {
  const expanded=!!document.fullscreenElement || $('camera-panel').classList.contains('expanded');
  $('fullscreen').setAttribute('aria-label',expanded?'Exit fullscreen':'Fullscreen view');
  $('fullscreen').title=expanded?'Exit fullscreen':'Fullscreen view';
}
$('fullscreen').addEventListener('click',async()=>{
  const panel=$('camera-panel');
  if(document.fullscreenElement){await document.exitFullscreen();return;}
  if(panel.classList.contains('expanded')){panel.classList.remove('expanded');document.body.classList.remove('expanded-view');syncFullscreen();return;}
  try {if(!panel.requestFullscreen)throw new Error('Fullscreen unavailable');await panel.requestFullscreen();}
  catch {panel.classList.add('expanded');document.body.classList.add('expanded-view');syncFullscreen();}
});
document.addEventListener('fullscreenchange',syncFullscreen);
document.addEventListener('keydown',event=>{
  if(event.key==='Escape' && $('camera-panel').classList.contains('expanded')){$('camera-panel').classList.remove('expanded');document.body.classList.remove('expanded-view');syncFullscreen();}
  if(event.repeat || event.altKey || event.ctrlKey || event.metaKey || event.target.closest('input,select,button,summary,a,[contenteditable]'))return;
  if(event.code==='Space'){event.preventDefault();($('stop').disabled?$('start'):$('stop')).click();}
  if(event.key.toLowerCase()==='p')$('pause').click();
  if(event.key.toLowerCase()==='f')$('fullscreen').click();
});
window.addEventListener('pagehide',()=>stop());
document.addEventListener('visibilitychange',()=>{if(document.hidden && (running || stream))stop('Camera paused while this tab is hidden. Restart when ready.');});
