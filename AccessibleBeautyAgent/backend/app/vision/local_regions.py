"""RAM-only local quality and uncalibrated color measurements."""
import cv2
import numpy as np

from app.vision.local_landmarks import LocalLandmarks
from app.vision.makeup_observation import observe_makeup


class LocalRegionAnalyzer:
    def __init__(self, gate):
        self.gate = gate
        self.landmarks = LocalLandmarks()

    def analyze(self, raw, baseline=None, target='blush'):
        detected = self.landmarks.detect(raw)
        if detected is None:
            result = self.proxy(raw)
            result['source'] = 'local_opencv_proxy'
        else:
            result = observe_makeup(raw, detected, target, baseline)
            result['source'] = 'local_mediapipe'
        result['landmark_status'] = self.landmarks.status
        result['landmark_count'] = result.get('geometry', {}).get('landmark_count', 0)
        result['quality'] = {
            'usable': result['gate']['gate_pass'],
            'warnings': result['quality_warnings'],
        }
        return result

    def proxy(self, raw):
        gate = self.gate.evaluate(raw)
        warnings = ['landmark_model_unavailable']
        if not gate['gate_pass']:
            count = gate.get('face_count')
            reason = ('no_face' if count == 0 else 'multiple_faces' if count and count > 1 else
                      'lighting' if gate.get('lighting_ok') is False else
                      'face_size' if gate.get('face_size_ok') is False else
                      'pose_or_occlusion' if gate.get('occlusion_warning') else
                      'blur' if gate.get('blur_score', 20) < 20 else 'quality_gate_failed')
            warnings.append(reason)
        result = {
            'status': 'UNCERTAIN', 'confidence': None, 'calibrated': False, 'simulated': False,
            'method': 'opencv_face_box_region_proxy', 'regions': {}, 'measurement': None,
            'comparison': None, 'gate': gate, 'quality_warnings': warnings,
            'assessment': {'status': 'uncertain', 'scope': 'coarse_color_proxy_only'},
            'message': '本地关键点模型不可用，仅提供画面质量和区域代理数值，不作前后比较。',
            'message_en': 'The local landmark model is unavailable. Only image quality and coarse color values are available; before/after comparison is unavailable.',
        }
        if not gate['gate_pass'] or not gate.get('face_box'):
            detail = gate.get('failure_reason') or '画面中未找到可靠的面部区域。'
            result['message'] = '本地关键点模型不可用，画面质量检查未通过。' + detail
            result['message_en'] = 'The local landmark model is unavailable and the quality check did not pass. Capture one clear, unobstructed face in even light.'
            return result
        pixels = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
        if pixels is None:
            raise ValueError('Invalid image')
        x, y, width, height = gate['face_box']
        image_height, image_width = pixels.shape[:2]
        if min(x, y) < 0 or min(width, height) <= 0 or x + width > image_width or y + height > image_height:
            raise ValueError('Invalid face geometry')
        lab = cv2.cvtColor(pixels, cv2.COLOR_BGR2LAB)
        # CSS preview mirroring does not change the captured camera pixels.
        boxes = {'left_cheek': (.65, .48, .86, .68), 'right_cheek': (.14, .48, .35, .68),
                 'lip_proxy': (.33, .70, .67, .84)}
        for name, (a, b, c, d) in boxes.items():
            region = lab[y + int(height * b):y + int(height * d), x + int(width * a):x + int(width * c)]
            if not region.size:
                continue
            values = np.median(region.reshape(-1, 3), axis=0)
            result['regions'][name] = {
                'lightness': round(float(values[0]), 3),
                'redness': round(float(values[1]) - 128, 3),
                'yellow_blue': round(float(values[2]) - 128, 3),
                'area': int(region.shape[0] * region.shape[1]),
            }
        return result
