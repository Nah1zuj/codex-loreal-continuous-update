"""RAM-only face-box proxy measurements, never a calibrated makeup classifier."""
import cv2,numpy as np

class LocalRegionAnalyzer:
    def __init__(self,gate):
        self.gate=gate
        from app.vision.local_landmarks import LocalLandmarks
        self.landmarks=LocalLandmarks()
    def analyze(self,raw,baseline=None,target='blush'):
        detected=self.landmarks.detect(raw)
        if detected is not None:
            from app.vision.makeup_observation import observe_makeup
            result=observe_makeup(raw,detected,target,baseline)
            result['landmark_status']=self.landmarks.status
            result['landmark_count']=result['geometry'].get('landmark_count',0)
            return result
        gate=self.gate.evaluate(raw)
        result={'status':'UNCERTAIN','confidence':None,'calibrated':False,'method':'opencv_face_box_region_proxy','regions':{},'measurement':None,'comparison':None,'gate':gate,'message':'本地颜色测量尚未校准，不能据此判断是否需要补色。'}
        if not gate['gate_pass'] or not gate.get('face_box'):
            result['message']=gate.get('failure_reason') or 'Face geometry unavailable'
            return result
        pixels=cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_COLOR)
        if pixels is None:raise ValueError('Invalid image')
        x,y,w,h=gate['face_box'];height,width=pixels.shape[:2]
        if x<0 or y<0 or w<=0 or h<=0 or x+w>width or y+h>height:raise ValueError('Invalid face geometry')
        lab=cv2.cvtColor(pixels,cv2.COLOR_BGR2LAB)
        # Captured pixels are unmirrored: image-right is the person's left.
        # CSS preview mirroring must not swap spoken body directions.
        boxes={'left_cheek':(.65,.48,.86,.68),'right_cheek':(.14,.48,.35,.68),'lip_proxy':(.33,.70,.67,.84)}
        for name,(a,b,c,d) in boxes.items():
            region=lab[y+int(h*b):y+int(h*d),x+int(w*a):x+int(w*c)]
            values=np.median(region.reshape(-1,3),axis=0)
            result['regions'][name]={'lightness':round(float(values[0]),3),'redness':round(float(values[1])-128,3),'yellow_blue':round(float(values[2])-128,3),'area':int(region.shape[0]*region.shape[1])}
        result['measurement']={'regions':result['regions'],'face_ratio':w*h/(width*height),'lighting':float(np.mean(lab[y:y+h,x:x+w,0]))}
        result['landmark_status']=self.landmarks.status
        result['landmark_count']=0
        if detected and detected['face_count']==1:
            from app.vision.local_landmarks import region_measurements
            try:
                result['regions'],result['measurement'],result['landmark_count']=region_measurements(raw,detected['points'])
                result['method']='mediapipe_landmark_relative_color_measurement'
            except ValueError:
                result['regions']={};result['measurement']=None;result['message']='关键点超出画面；无法比较妆效。';return result
        elif detected:
            result['regions']={};result['measurement']=None;result['message']='关键点检测没有找到唯一人脸；无法比较妆效。';return result
        if baseline:
            comparable=baseline.get('method')==result['method'] and abs(baseline['lighting']-result['measurement']['lighting'])<15 and abs(baseline['face_ratio']-result['measurement']['face_ratio'])<.08
            result['comparison']={'comparable':comparable,'redness_delta':{name:round(row['redness']-baseline['regions'][name]['redness'],3) for name,row in result['regions'].items()} if comparable else {},'interpretation':'measurement_only_not_makeup_decision'}
        result['measurement']['method']=result['method']
        return result
