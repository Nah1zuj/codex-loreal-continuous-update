"""Interpretable, uncalibrated local appearance rules; no beauty/coverage verdict.

LAB uses float BGR [0,1] -> L [0,100], a/b approximately [-127,127].
Thresholds are engineering defaults, NOT validated probabilities. See vision docs.
"""
import math
import cv2
import numpy as np

VERSION='trace-local-lab-v1'
THRESHOLDS={'min_face_ratio':.08,'max_face_ratio':.85,'min_luminance':45,
            'max_luminance':220,'min_sharpness':20,'max_cheek_light_delta':12,
            'max_nose_offset':.22,'max_roll_degrees':20,'color_difference':3,
            'comparison_light_delta':8,'comparison_size_delta':.04,'comparison_pose_delta':.08}

def empty(reason='face_unavailable'):
    return {'status':'UNCERTAIN','confidence':None,'calibrated':False,'simulated':False,
            'method':'mediapipe_masked_lab','evaluation_version':VERSION,'regions':{},
            'geometry':{'face_detected':False,'face_count':0,'detection_quality':None},
            'measurement':None,'comparison':None,'quality_warnings':[reason],
            'assessment':{'status':'uncertain','scope':'relative_cheek_color_not_makeup_coverage'},
            'gate':{'gate_pass':False,'failure_reason':reason,'method':'mediapipe_image_quality'},
            'message':'我现在还看不清楚。请保持单张正面人脸、光线均匀，再检查一次。',
            'message_en':'I cannot see clearly yet. Keep one face front-facing in even light and check again.'}

def observe_makeup(raw,detected,target='blush',previous=None):
    result=empty();count=detected.get('face_count',0)
    result['geometry']['face_count']=count
    if count!=1:
        result['quality_warnings']=['no_face' if not count else 'multiple_faces'];return result
    pixels=cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_COLOR)
    points=np.asarray(detected.get('points',[]),float)
    if pixels is None or points.ndim!=2 or points.shape[0]<468 or points.shape[1]!=3 or not np.isfinite(points).all() or (points[:,:2]<0).any() or (points[:,:2]>1).any():
        result['quality_warnings']=['invalid_landmarks'];return result
    height,width=pixels.shape[:2];span=np.ptp(points[:,:2],axis=0);low=points[:,:2].min(axis=0)
    ratio=float(np.prod(span));eyes=points[[33,263],:2];eyes=eyes[np.argsort(eyes[:,0])]
    eye_span=float(eyes[1,0]-eyes[0,0]);nose_offset=float((points[1,0]-eyes[:,0].mean())/max(eye_span,.001))
    roll=math.degrees(math.atan2(float(eyes[1,1]-eyes[0,1])*height,eye_span*width))
    geometry={'face_detected':True,'face_count':1,'face_bounds':[float(low[0]),float(low[1]),float(span[0]),float(span[1])],
              'head_pose':{'roll':round(roll,2),'yaw_proxy':round(nose_offset,3),'method':'2d_eye_nose_geometry_not_calibrated_angles'},
              'detection_quality':None,'landmark_count':len(points)}
    result['geometry']=geometry
    x0,y0=(low*[width,height]).astype(int);x1,y1=np.minimum([width,height],np.ceil((low+span)*[width,height])).astype(int)
    face=pixels[y0:y1,x0:x1]
    if not face.size:return empty('invalid_bounds')
    gray=cv2.cvtColor(face,cv2.COLOR_BGR2GRAY);brightness=float(gray.mean());sharpness=float(cv2.Laplacian(gray,cv2.CV_64F).var())
    warnings=[]
    if not THRESHOLDS['min_face_ratio']<=ratio<=THRESHOLDS['max_face_ratio']:warnings.append('face_size')
    if not THRESHOLDS['min_luminance']<=brightness<=THRESHOLDS['max_luminance'] or np.mean(gray<25)>.3 or np.mean(gray>245)>.2:warnings.append('lighting')
    if sharpness<THRESHOLDS['min_sharpness']:warnings.append('blur')
    if eye_span<span[0]*.3 or abs(nose_offset)>THRESHOLDS['max_nose_offset'] or abs(roll)>THRESHOLDS['max_roll_degrees']:warnings.append('pose')
    lab=cv2.cvtColor(pixels.astype(np.float32)/255,cv2.COLOR_BGR2LAB)
    cheeks=points[[50,280],:2];cheeks=cheeks[np.argsort(cheeks[:,0])]
    # Raw frames are unmirrored. Image-right = subject-left for accepted frontal pose.
    centers={'right_cheek':cheeks[0],'left_cheek':cheeks[1],'lip_proxy':points[[13,14],:2].mean(axis=0)}
    regions={}
    for name,center in centers.items():
        rx=max(3,int(span[0]*width*(.07 if name!='lip_proxy' else .11)))
        ry=max(3,int(span[1]*height*(.045 if name!='lip_proxy' else .018)))
        cx,cy=np.round(center*[width,height]).astype(int)
        xa,xb=max(0,cx-rx),min(width,cx+rx+1);ya,yb=max(0,cy-ry),min(height,cy+ry+1)
        yy,xx=np.mgrid[ya:yb,xa:xb];mask=((xx-cx)/rx)**2+((yy-cy)/ry)**2<=1
        patch=lab[ya:yb,xa:xb];usable=mask&(patch[:,:,0]>10)&(patch[:,:,0]<92)
        if mask.sum()<20 or usable.sum()<mask.sum()*.65:warnings.append('region_occluded_or_clipped');continue
        values=patch[usable];median=np.median(values,axis=0)
        regions[name]={'lightness':round(float(median[0]),3),'redness':round(float(median[1]),3),'yellow_blue':round(float(median[2]),3),
                       'area':int(usable.sum()),'redness_iqr':round(float(np.percentile(values[:,1],75)-np.percentile(values[:,1],25)),3),
                       'highlight_filtered_ratio':round(float(1-usable.sum()/mask.sum()),3)}
    if len(regions)!=3:warnings.append('region_missing')
    if 'left_cheek' in regions and 'right_cheek' in regions and abs(regions['left_cheek']['lightness']-regions['right_cheek']['lightness'])>THRESHOLDS['max_cheek_light_delta']:warnings.append('asymmetric_lighting')
    result['gate']={'gate_pass':not warnings,'failure_reason':warnings[0] if warnings else None,'method':'mediapipe_image_quality',
                    'blur_score':round(sharpness,2),'lighting_luminance':round(brightness,2)}
    result['quality_warnings']=list(dict.fromkeys(warnings));result['regions']=regions
    if warnings:
        result['message']='当前画面不适合可靠比较：'+('两侧光线差异较大。' if 'asymmetric_lighting' in warnings else '请面向镜头、保持脸部无遮挡，并调整光线和清晰度。')+'我还不能判断妆效，请再检查一次。'
        result['message_en']='This frame is unsuitable for comparison. Keep your face front-facing, clear and evenly lit, then check again. No makeup conclusion was made.'
        return result
    difference=regions['left_cheek']['redness']-regions['right_cheek']['redness']
    result['measurement']={'method':result['method'],'version':VERSION,'target':target,'lighting':(regions['left_cheek']['lightness']+regions['right_cheek']['lightness'])/2,
                           'face_ratio':ratio,'pose':nose_offset,'bounds':geometry['face_bounds'],'regions':regions,'difference':difference}
    result['assessment']['measured_features']={'left_minus_right_lab_a':round(difference,3),'imbalance_proxy':round(abs(difference),3)}
    if target=='lips':
        result['assessment']['scope']='lip_region_color_only_not_product_coverage'
        result['message']='识别到了唇部区域，可以比较区域颜色数值；原本唇色、光线与口红都可能影响颜色，我暂时不能确认是否完整覆盖。'
        result['message_en']='The lip region is located and color measurements are available. Natural lip color, light and lipstick all affect them; full coverage cannot be confirmed.'
    else:
        result['assessment']['status']='approximately_balanced' if abs(difference)<=THRESHOLDS['color_difference'] else 'left_more_prominent' if difference>0 else 'right_more_prominent'
        result['status']='HEURISTIC_OBSERVATION'
        side='左侧' if difference>0 else '右侧';side_en='left' if difference>0 else 'right'
        result['message']=('这张画面中，两侧脸颊的红色分量接近。' if abs(difference)<=3 else f'这张画面中，你的{side}脸颊红色分量更明显。')+'这是未校准的区域颜色比较，不能确认差异来自腮红，也不表示必须修改。你希望保留现在的表达，还是调整后再比较？'
        result['message_en']=('The cheek red components are similar in this frame. ' if abs(difference)<=3 else f'Your {side_en} cheek has a more prominent red component in this frame. ')+'This uncalibrated color comparison cannot attribute the difference to blush and does not require correction. Keep this expression or adjust and recheck?'
    if previous:
        comparable=previous.get('version')==VERSION and previous.get('target')==target and abs(previous['lighting']-result['measurement']['lighting'])<=THRESHOLDS['comparison_light_delta'] and abs(previous['face_ratio']-ratio)<=THRESHOLDS['comparison_size_delta'] and abs(previous['pose']-nose_offset)<=THRESHOLDS['comparison_pose_delta'] and max(abs(a-b) for a,b in zip(previous['bounds'],geometry['face_bounds']))<.06
        result['comparison']={'comparable':comparable,'claim':'color_difference_change_not_makeup_improvement','redness_delta':{},'imbalance_delta':None}
        if comparable:
            change=round(abs(difference)-abs(previous['difference']),3)
            result['comparison'].update(imbalance_delta=change,redness_delta={name:round(row['redness']-previous['regions'][name]['redness'],3) for name,row in regions.items()})
            result['message']+=(' 与上一张可比画面相比，两侧颜色差距'+('减小了。' if change<-.5 else '增大了。' if change>.5 else '变化不明显。')+'这不等同于妆效改善。') if target!='lips' else ' 与上一张画面的唇部颜色变化数值可在详情查看，不代表覆盖改善。'
            result['message_en']+=' Compared with the previous compatible frame, '+('the cheek color gap decreased. ' if change<-.5 else 'the cheek color gap increased. ' if change>.5 else 'the cheek color gap changed little. ')+'This is not proof of makeup improvement.' if target!='lips' else ' Lip color changes are in the details and do not establish improved coverage.'
        else:
            result['message']+=' 光线、位置或角度与上一张不够接近，不能作前后比较。'
            result['message_en']+=' Light, position or pose differs too much from the previous frame for a before/after comparison.'
    return result
