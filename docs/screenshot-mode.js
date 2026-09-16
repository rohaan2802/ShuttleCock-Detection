const shot = new URLSearchParams(location.search).get('shot');

if (shot) {
  window.addEventListener('DOMContentLoaded', () => {
    const params = new URLSearchParams(location.search);
    const focus = params.get('focus');
    if (focus) document.body.dataset.shotFocus = focus;
    const $ = (id) => document.getElementById(id);
    const text = (id, value) => {
      const element = $(id);
      if (element) element.textContent = value;
    };

    const panel = $('camera-panel');
    const stage = $('stage');
    const demoFeed = document.createElement('div');
    demoFeed.id = 'demo-feed';
    demoFeed.innerHTML = `
      <div class="demo-court"></div>
      <div class="demo-line demo-midline"></div>
      <div class="demo-line demo-net"></div>
      <div class="demo-box demo-box-primary"><span>Shuttle 91%</span></div>
      <div class="demo-box demo-box-secondary"><span>Shuttle 76%</span></div>
    `;
    stage.prepend(demoFeed);

    for (let i = 0; i < 60; i += 1) {
      const speck = document.createElement('i');
      speck.style.left = `${(i * 13) % 100}%`;
      speck.style.top = `${(i * 29) % 100}%`;
      demoFeed.appendChild(speck);
    }

    const style = document.createElement('style');
    style.textContent = `
      #demo-feed{position:absolute;inset:0;z-index:0;overflow:hidden;background:linear-gradient(135deg,#10243a,#0a3f3c 52%,#15132d)}
      #demo-feed[hidden]{display:none}
      #demo-feed i{position:absolute;width:2px;height:2px;background:rgba(255,255,255,.18)}
      .demo-court{position:absolute;inset:11% 9%;border:3px solid rgba(94,234,212,.45)}
      .demo-line{position:absolute;border-color:rgba(94,234,212,.45)}
      .demo-midline{left:50%;top:11%;bottom:15%;border-left:3px solid rgba(94,234,212,.45)}
      .demo-net{left:9%;right:9%;top:50%;border-top:3px solid rgba(94,234,212,.45)}
      .demo-box{position:absolute;border:5px solid #5eead4;box-shadow:0 0 25px rgba(94,234,212,.25)}
      .demo-box span{position:absolute;left:0;top:-36px;background:#5eead4;color:#08131c;font:700 18px sans-serif;padding:6px 10px;white-space:nowrap}
      .demo-box-primary{left:61%;top:31%;width:10%;height:25%}
      .demo-box-secondary{left:27%;top:59%;width:8%;height:18%;border-color:#9e95ff;box-shadow:none}
      .demo-box-secondary span{top:-34px;background:#9e95ff;font-size:16px}
      #empty,#view,#grid-overlay,#paused-overlay{z-index:2}
      body[data-shot-focus="aside"] .intro,body[data-shot-focus="aside"] .camera-panel{display:none}
      body[data-shot-focus="aside"] .workspace{display:block}
      body[data-shot-focus="metrics"] .intro,body[data-shot-focus="metrics"] .workspace{display:none}
      body[data-shot-focus="metrics"] .metrics{margin-top:0}
      @media(max-width:760px){.demo-box span{font-size:12px;top:-27px;padding:4px 6px}.demo-box-secondary span{font-size:11px;top:-25px}.demo-box{border-width:4px}.demo-box-primary{left:67%;width:13%}.demo-box-secondary{left:33%;width:11%}}
    `;
    document.head.appendChild(style);

    const setIdle = () => {
      demoFeed.hidden = true;
      $('view').hidden = true;
      $('empty').hidden = false;
      panel.dataset.state = 'idle';
      $('indicator').classList.remove('live');
      text('mode-badge', 'STANDBY');
      text('resolution', 'CAMERA OFF');
      text('status', 'Ready when you are.');
      text('count', '-');
      text('fps', '- FPS');
      text('frames', '0');
      text('elapsed', '00:00');
      text('session-note', 'Waiting to start');
      text('coordinates', 'X - / Y -');
      text('match', 'Highest-confidence match');
      text('target-state', 'NO TARGET');
      $('target-dot').hidden = true;
      $('confidence-bar').style.width = '0%';
    };

    const setLive = (paused = false) => {
      demoFeed.hidden = false;
      $('view').hidden = true;
      $('empty').hidden = true;
      panel.dataset.state = paused ? 'paused' : 'live';
      $('indicator').classList.add('live');
      text('mode-badge', paused ? 'PAUSED' : 'LIVE');
      text('resolution', '1280 x 720');
      text('status', paused ? 'Detection paused. Camera remains on.' : 'Shuttlecock detected.');
      text('count', '2');
      text('fps', paused ? '- FPS' : '18.7 FPS');
      text('frames', '1,248');
      text('elapsed', '03:42');
      text('session-note', paused ? 'Detection paused - camera on' : 'Camera active');
      text('coordinates', 'X 632 / Y 236');
      text('match', '91% confidence - highest match');
      text('target-state', paused ? 'PAUSED' : 'TRACKING');
      $('target-dot').hidden = false;
      $('target-dot').style.left = '66%';
      $('target-dot').style.top = '43%';
      $('confidence-bar').style.width = '91%';
      $('grid').checked = true;
      $('grid-overlay').hidden = false;
      $('paused-overlay').hidden = !paused;
      $('start').disabled = true;
      $('stop').disabled = false;
      $('pause').disabled = false;
      $('snapshot').disabled = false;
      $('camera').disabled = true;
    };

    setIdle();
    if (shot === 'controls') {
      $('confidence').value = '42';
      text('confidence-value', '42%');
      $('confidence').style.setProperty('--progress', '40%');
      $('grid').checked = true;
      $('mirror').checked = true;
      text('status', 'Adjust threshold, guides, mirroring, or camera source before starting.');
    }
    if (shot === 'live' || shot === 'metrics') setLive(false);
    if (shot === 'paused') setLive(true);
    const tips = document.querySelector('details.tips');
    if (tips) tips.open = shot === 'controls' || shot === 'metrics';
    const scrollY = Number(params.get('scroll') || 0);
    if (Number.isFinite(scrollY) && scrollY > 0) {
      requestAnimationFrame(() => window.scrollTo(0, scrollY));
    }
  });
}
