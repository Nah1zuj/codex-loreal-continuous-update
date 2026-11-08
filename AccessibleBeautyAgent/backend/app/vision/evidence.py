"""Only bounded local measurements may enter text-model context; never images/landmarks."""
import time

def fresh_visual_summary(observation):
    if not observation or observation.get('simulated') or not time.time()-30 <= observation.get('captured_at',0) <= time.time()+5:
        return None
    keys=('target','status','confidence','calibrated','method','evaluation_version','regions','comparison','source','quality','quality_warnings','assessment','captured_at','observation_id','frame_id','knowledge')
    return {key:observation[key] for key in keys if key in observation}
