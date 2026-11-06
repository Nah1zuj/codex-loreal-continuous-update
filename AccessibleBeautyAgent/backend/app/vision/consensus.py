from collections import Counter
from app.schemas.models import VisualResult

def aggregate(frames, minimum=.6):
    if len(frames) != 3:
        raise ValueError('Exactly three visual results required')
    validated = [VisualResult.model_validate(f).model_dump() for f in frames]
    if len({f['task'] for f in validated}) != 1:
        raise ValueError('All frames must use the same task')
    reliable = [f for f in validated if f['confidence']>=minimum and f['status']!='UNCERTAIN' and f['image_quality']!='poor']
    votes = Counter(f['status'] for f in reliable)
    status,count = votes.most_common(1)[0] if votes else ('UNCERTAIN',0)
    winners = [f for f in reliable if f['status']==status]
    # Disagreement/uncertainty penalizes the confidence of majority frames.
    confidence = (sum(f['confidence'] for f in winners)/count)*(1-.15*(3-count)) if count>=2 else .0
    if count < 2 or confidence < minimum:
        status = 'UNCERTAIN'
    return {**VisualResult(task=validated[0]['task'],status=status,confidence=round(confidence,3),image_quality='good' if all(f['image_quality']=='good' for f in validated) else 'moderate',simulated=any(f['simulated'] for f in validated)).model_dump(), 'frame_results':validated,'agreement':count/3}
