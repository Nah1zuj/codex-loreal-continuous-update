"""Optional official MediaPipe IMAGE inference; bytes remain in RAM, no networking."""
import hashlib,json
from pathlib import Path
from threading import RLock
import cv2,numpy as np

MODEL=Path(__file__).resolve().parents[3]/'work/models/face_landmarker.task'
class LocalLandmarks:
    def __init__(self):self.detector=None;self.lock=RLock();self.status='not_initialized'
    def close(self):
        with self.lock:
            if self.detector is not None:self.detector.close();self.detector=None
    def detect(self,raw):
        with self.lock:
            if self.detector is None:
                if not MODEL.is_file():self.status='model_missing';return None
                try:
                    manifest=json.loads(Path(__file__).with_name('face-landmarker.json').read_text(encoding='utf-8'))
                    if hashlib.sha256(MODEL.read_bytes()).hexdigest()!=manifest['sha256']:self.status='model_integrity_failed';return None
                    import mediapipe as mp
                    self.mp=mp
                    options=mp.tasks.vision.FaceLandmarkerOptions(base_options=mp.tasks.BaseOptions(model_asset_path=str(MODEL)),running_mode=mp.tasks.vision.RunningMode.IMAGE,num_faces=2,output_face_blendshapes=False,output_facial_transformation_matrixes=False)
                    self.detector=mp.tasks.vision.FaceLandmarker.create_from_options(options)
                except (ImportError,OSError,RuntimeError,ValueError,KeyError):self.status='runtime_unavailable';return None
            pixels=cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_COLOR)
            if pixels is None:raise ValueError('Invalid image')
            image=self.mp.Image(image_format=self.mp.ImageFormat.SRGB,data=cv2.cvtColor(pixels,cv2.COLOR_BGR2RGB))
            try:
                result=self.detector.detect(image)
            except (RuntimeError, ValueError):
                self.close()
                self.status='runtime_unavailable'
                return None
            self.status='ready'
            if len(result.face_landmarks)!=1:return {'face_count':len(result.face_landmarks),'points':[]}
            return {'face_count':1,'points':[(p.x,p.y,p.z) for p in result.face_landmarks[0]]}

def region_measurements(raw,landmarks):
    """Uncalibrated landmark-relative patches; return numbers, never a makeup verdict."""
    pixels=cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_COLOR)
    height,width=pixels.shape[:2];points=np.asarray(landmarks,dtype=float)
    if points.shape[0]<468 or not np.isfinite(points).all():raise ValueError('Invalid landmarks')
    if np.any(points[:,:2]<0) or np.any(points[:,:2]>1):raise ValueError('Face extends beyond frame')
    lab=cv2.cvtColor(pixels,cv2.COLOR_BGR2LAB)
    span=np.ptp(points[:,:2],axis=0)
    # Choose physical left/right by unmirrored image x, not the preview transform.
    cheeks=sorted([points[50,:2],points[280,:2]],key=lambda p:p[0])
    centers={'right_cheek':cheeks[0],'left_cheek':cheeks[1],'lip_proxy':(points[13,:2]+points[14,:2])/2}
    regions={}
    for name,center in centers.items():
        rx=max(2,int(width*span[0]*(.04 if name=='lip_proxy' else .07)));ry=max(2,int(height*span[1]*.025))
        cx,cy=int(center[0]*width),int(center[1]*height)
        patch=lab[max(0,cy-ry):min(height,cy+ry+1),max(0,cx-rx):min(width,cx+rx+1)]
        if patch.size==0:raise ValueError('Region outside frame')
        values=np.median(patch.reshape(-1,3),axis=0)
        regions[name]={'lightness':round(float(values[0]),3),'redness':round(float(values[1])-128,3),'yellow_blue':round(float(values[2])-128,3),'area':int(patch.shape[0]*patch.shape[1])}
    left,right=regions['left_cheek'],regions['right_cheek']
    return regions,{'face_ratio':float(span[0]*span[1]),'lighting':float((left['lightness']+right['lightness'])/2),'regions':regions},len(points)
