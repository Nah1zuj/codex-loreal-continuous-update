import base64
import binascii
import cv2
import numpy as np

def decode_image(value):
    if len(value) > 3_000_000:
        raise ValueError('图片过大，请缩小至最长边 1024 像素。')
    try:
        if value.startswith('data:'):
            header, value = value.split(',',1)
            if header not in ('data:image/jpeg;base64','data:image/png;base64'):
                raise ValueError('Only JPEG/PNG data URLs supported')
        raw = base64.b64decode(value,validate=True)
        # Inspect dimensions before decoding untrusted pixels.
        from PIL import Image
        import io
        with Image.open(io.BytesIO(raw)) as im:
            if im.width > 2048 or im.height > 2048 or min(im.size) < 32:
                raise ValueError('Image dimensions must be 32–2048px')
            if im.format not in ('JPEG','PNG'):
                raise ValueError('Unsupported image format')
        return raw
    except (binascii.Error, OSError, ValueError) as exc:
        raise ValueError('图片格式无效，请重新拍摄。') from exc

class LocalFaceGate:
    """Conservative Haar face + eye-landmark proxy. Not a makeup detector.

    Pose and occlusion are coarse proxies; false rejects can occur (glasses,
    camera framing, non-frontal faces). A failed gate never reaches vision.
    """
    def __init__(self):
        self.faces = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eyes = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        if self.faces.empty() or self.eyes.empty():
            raise RuntimeError('OpenCV local face/eye models unavailable')

    def evaluate(self, image):
        img = cv2.imdecode(np.frombuffer(image,dtype=np.uint8),cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError('无法解码图片。')
        gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
        detected = self.faces.detectMultiScale(gray,1.1,5,minSize=(60,60))
        result = {'face_count':len(detected),'face_detected':len(detected)>0,'face_size_ok':False,'pose_ok':False,'lighting_ok':False,'occlusion_warning':False,'lighting_score':0.,'pose_score':0.,'gate_pass':False,'failure_reason':None,'method':'opencv_haar_eye_proxy','simulated':False}
        if len(detected) != 1:
            result['failure_reason'] = '没有检测到单张正面人脸，请朝向镜头，并让脸完整进入画面。' if len(detected)==0 else '检测到多张人脸，请只保留你自己在画面中。'
            return result
        x,y,w,h = [int(n) for n in detected[0]]
        result['face_box']=[x,y,w,h]
        face = gray[y:y+h,x:x+w]
        ratio = w*h/(gray.shape[0]*gray.shape[1])
        result['face_size_ok'] = .08 <= ratio <= .85
        brightness = float(np.mean(face))
        dark = float(np.mean(face < 25))
        clipped = float(np.mean(face > 245))
        contrast = float(np.std(face))
        result['lighting_score'] = round(max(0,min(1,1-abs(brightness-135)/135)),3)
        result['lighting_ok'] = 50 <= brightness <= 215 and dark < .35 and clipped < .3 and contrast > 10
        eye_boxes = self.eyes.detectMultiScale(face[:int(h*.65)],1.1,4,minSize=(15,15))
        centers = [(ex+ew/2,ey+eh/2) for ex,ey,ew,eh in eye_boxes]
        eye_pair = None
        for a in centers:
            for b in centers:
                separation = abs(a[0]-b[0])/w
                if .2 <= separation <= .7 and abs(a[1]-b[1])/h < .13:
                    eye_pair = (a,b)
                    break
        result['pose_ok'] = eye_pair is not None
        result['pose_score'] = .8 if eye_pair else .25
        result['occlusion_warning'] = eye_pair is None
        sharpness = float(cv2.Laplacian(face,cv2.CV_64F).var())
        result['blur_score'] = round(sharpness,2)
        if not result['lighting_ok']:
            reason = '现在光线不足或过强，我无法可靠判断。请移到均匀明亮的位置。'
        elif not result['face_size_ok']:
            reason = '请调整和镜头的距离，让完整脸部占画面的大约三分之一。'
        elif not result['pose_ok']:
            reason = '我还不能确认正面姿态，请朝正前方，并让双眼区域无遮挡。'
        elif sharpness < 20:
            reason = '画面有些模糊，请稳住手机再拍一次。'
        else:
            reason = None
        result['gate_pass'] = reason is None
        result['failure_reason'] = reason
        return result

def demo_gate():
    return {'face_detected':True,'face_size_ok':True,'pose_ok':True,'lighting_ok':True,'occlusion_warning':False,'lighting_score':.9,'pose_score':.9,'gate_pass':True,'failure_reason':None,'method':'mock_demo','simulated':True}
