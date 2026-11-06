"""Select local video frames. Never sends frames to an AI provider."""
import argparse
import json
import uuid
from pathlib import Path
import cv2

ROOT=Path(__file__).resolve().parents[1]
def seconds(text):
    parts=[float(x) for x in text.split(':')]
    if len(parts)>3 or any(x<0 for x in parts):raise ValueError('时间格式应为 秒 / 分:秒 / 时:分:秒')
    value=0
    for part in parts:value=value*60+part
    return value

def extract(file,destination,interval=5,timestamps=None):
    if not destination.resolve().is_relative_to(ROOT.resolve()):raise ValueError('输出目录必须在项目内。')
    if interval<=0:raise ValueError('interval 必须大于 0。')
    cap=cv2.VideoCapture(str(file))
    if not cap.isOpened():raise ValueError('视频无法打开，请检查路径与格式。')
    try:
        fps=cap.get(cv2.CAP_PROP_FPS);frames=cap.get(cv2.CAP_PROP_FRAME_COUNT)
        if fps<=0 or frames<=0:raise ValueError('无法取得视频时长。')
        duration=frames/fps
        times=[seconds(x.strip()) for x in timestamps.split(',')] if timestamps else [i*interval for i in range(int(duration/interval)+1) if i*interval<duration]
        if len(times)>1000:raise ValueError('一次最多抽取 1000 帧，请增大 interval。')
        destination.mkdir(parents=True,exist_ok=True);results=[];errors=[]
        for t in times:
            if t>=duration:errors.append({'timestamp':t,'message':'时间超出视频时长'});continue
            cap.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,frame=cap.read()
            if not ok:errors.append({'timestamp':t,'message':'该帧读取失败'});continue
            target=destination/f'frame_{round(t*1000):09d}.jpg'
            if target.exists():errors.append({'timestamp':t,'message':'文件已存在，不覆盖'});continue
            ok,encoded=cv2.imencode('.jpg',frame,[cv2.IMWRITE_JPEG_QUALITY,90])
            if not ok:errors.append({'timestamp':t,'message':'编码失败'});continue
            target.write_bytes(encoded.tobytes())
            results.append({'source_video':str(file.resolve()),'timestamp':t,'actual_timestamp':cap.get(cv2.CAP_PROP_POS_MSEC)/1000,'frame_path':str(target.relative_to(ROOT)).replace('\\','/')})
        report={'source_video':str(file.resolve()),'duration_seconds':duration,'frames':results,'errors':errors,'ai_called':False}
        (destination/'metadata.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        return report
    finally:cap.release()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--file',type=Path,required=True);p.add_argument('--interval',type=float,default=5);p.add_argument('--timestamps');p.add_argument('--output',type=Path)
    a=p.parse_args();dest=a.output or ROOT/'data/references/frames'/('video_'+uuid.uuid4().hex[:8])
    r=extract(a.file,dest,a.interval,a.timestamps);print(f"Extracted={len(r['frames'])} errors={len(r['errors'])} -> {dest}")

if __name__=='__main__':main()
