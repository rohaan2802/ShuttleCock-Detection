"""Compare the browser export to the original checkpoint on repository images."""
import json
from pathlib import Path
import sys
import cv2
import numpy as np
import onnxruntime as ort
import torch
from ultralytics import YOLO
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from model_config import ROOT, MODEL_PATH, BROWSER_MODEL

torch.set_num_threads(2)
model = YOLO(str(MODEL_PATH))
model.fuse()
model.model.eval()
session = ort.InferenceSession(str(BROWSER_MODEL), providers=['CPUExecutionProvider'])
assert session.get_inputs()[0].shape == [1,3,320,320]
assert session.get_outputs()[0].shape == [1,5,2100]
sources = sorted((ROOT/'My Drive/ShuttleBot/runs/predict_test_v1').glob('*.jpg'))[:3]
assert sources, 'Repository validation images missing'
out=ROOT/'.test-output'
out.mkdir(exist_ok=True)
reports=[]
for index,path in enumerate(sources):
    image=cv2.imread(str(path))
    h,w=image.shape[:2];r=min(320/w,320/h)
    nw,nh=round(w*r),round(h*r);left,top=round((320-nw)/2-.1),round((320-nh)/2-.1)
    padded=np.full((320,320,3),114,dtype=np.uint8)
    padded[top:top+nh,left:left+nw]=cv2.resize(cv2.cvtColor(image,cv2.COLOR_BGR2RGB),(nw,nh))
    data=np.ascontiguousarray(padded.transpose(2,0,1)[None],dtype=np.float32)/255
    with torch.no_grad():
        expected=model.model(torch.from_numpy(data))[0].numpy()
    actual=session.run(None,{'images':data})[0]
    np.testing.assert_allclose(actual,expected,rtol=1e-3,atol=2e-3)
    reports.append({'sample':path.name,'max_absolute_error':float(np.max(np.abs(actual-expected))),
        'candidates_above_35_percent':int((actual[0,4]>=.35).sum())})
    if index==0:
        data.tofile(out/'input.f32')
        actual.tofile(out/'expected.f32')
        cv2.imwrite(str(out/'sample.jpg'),image)
(out/'export-verification.json').write_text(json.dumps(reports,indent=2))
print(json.dumps(reports,indent=2))
