"""Download the official model bundle only. No camera, user image or remote inference."""
import hashlib,json,urllib.request
from pathlib import Path

URL='https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task'
ROOT=Path(__file__).resolve().parents[1]
def main():
    directory=ROOT/'work/models';directory.mkdir(parents=True,exist_ok=True)
    with urllib.request.urlopen(URL,timeout=30) as response:raw=response.read(40_000_001)
    if len(raw)>40_000_000 or len(raw)<100_000:raise ValueError('Unexpected model size')
    digest=hashlib.sha256(raw).hexdigest()
    (directory/'face_landmarker.task').write_bytes(raw)
    (directory/'face_landmarker.manifest.json').write_text(json.dumps({'source':URL,'sha256':digest,'bytes':len(raw),'purpose':'local facial geometry only; makeup accuracy not calibrated'},indent=2),encoding='utf-8')
    print('Official local model downloaded; bytes='+str(len(raw))+' sha256='+digest)
if __name__=='__main__':main()
