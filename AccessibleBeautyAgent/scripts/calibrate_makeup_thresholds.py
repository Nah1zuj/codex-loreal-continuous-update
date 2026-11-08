"""Recommend a color-difference threshold offline; never activate it in production."""
import argparse,json,math
from pathlib import Path

def calibrate(rows):
    permitted=[r for r in rows if r.get('sourceType')=='real_labeled' and r.get('consentStatus')=='granted' and 'calibrate' in r.get('allowedUse',[]) and r.get('makeupRegion')=='blush']
    valid=[r for r in permitted if r.get('humanLabels',{}).get('classification') in {'approximately_balanced','left_more_prominent','right_more_prominent'} and type(r.get('modelPredictions',{}).get('features',{}).get('left_minus_right_lab_a')) in (float,int) and math.isfinite(r['modelPredictions']['features']['left_minus_right_lab_a'])]
    if len(valid)<30:return {'status':'NOT_CALIBRATED','reason':'Need at least 30 authorized real labeled calibration records','records':len(valid),'activated':False}
    versions={r.get('modelVersion') for r in valid}
    if len(versions)!=1:return {'status':'NOT_CALIBRATED','reason':'Separate model versions before calibration','records':len(valid),'activated':False}
    candidates=[]
    for threshold in [x*.5 for x in range(2,21)]:
        correct=0
        for row in valid:
            delta=row['modelPredictions']['features']['left_minus_right_lab_a']
            pred='approximately_balanced' if abs(delta)<=threshold else 'left_more_prominent' if delta>0 else 'right_more_prominent'
            correct+=pred==row['humanLabels']['classification']
        candidates.append({'threshold':threshold,'calibration_set_agreement':correct/len(valid)})
    best=max(candidates,key=lambda value:value['calibration_set_agreement'])
    return {'status':'CANDIDATE_ONLY','candidate':best,'records':len(valid),'activated':False,'next':'Evaluate on independently labeled holdout and lighting/skin-tone strata before adoption.'}
def main():
    parser=argparse.ArgumentParser();parser.add_argument('samples',type=Path);args=parser.parse_args()
    from evaluate_makeup_vision import validate_rows
    rows=[json.loads(line,parse_constant=lambda value:(_ for _ in ()).throw(ValueError('Non-finite JSON number'))) for line in args.samples.read_text(encoding='utf-8').splitlines() if line.strip()]
    validate_rows(rows)
    print(json.dumps(calibrate(rows),indent=2))
if __name__=='__main__':main()
