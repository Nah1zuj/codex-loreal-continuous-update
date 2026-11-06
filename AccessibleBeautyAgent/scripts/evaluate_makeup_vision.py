"""Offline label-only evaluation. Never fetch images, train or invent ground truth."""
import argparse,json,math
from collections import Counter,defaultdict
from pathlib import Path

def iou(a,b):
    if len(a)!=4 or len(b)!=4 or not all(math.isfinite(x) for x in a+b) or min(a[2:]+b[2:])<=0:raise ValueError('Invalid x,y,width,height box')
    overlap=max(0,min(a[0]+a[2],b[0]+b[2])-max(a[0],b[0]))*max(0,min(a[1]+a[3],b[1]+b[3])-max(a[1],b[1]))
    return overlap/(a[2]*a[3]+b[2]*b[3]-overlap)
def evaluate(rows):
    permitted=[r for r in rows if r.get('consentStatus')=='granted' and 'evaluate' in r.get('allowedUse',[]) and r.get('sourceType')=='real_labeled']
    labeled=[r for r in permitted if r.get('humanLabels') and r.get('modelPredictions')]
    if not labeled:return {'status':'NOT_EVALUATED','reason':'No authorized real labeled samples','real_labeled_samples':0}
    classified=[r for r in labeled if 'classification' in r['humanLabels'] and 'classification' in r['modelPredictions']]
    pairs=Counter((r['humanLabels']['classification'],r['modelPredictions']['classification']) for r in classified)
    classes=sorted({c for pair in pairs for c in pair});per_class={}
    for c in classes:
        tp=pairs[c,c];fp=sum(n for (label,pred),n in pairs.items() if pred==c and label!=c);fn=sum(n for (label,pred),n in pairs.items() if label==c and pred!=c)
        per_class[c]={'true_positive':tp,'false_positive':fp,'false_negative':fn,'precision':tp/(tp+fp) if tp+fp else None,'recall':tp/(tp+fn) if tp+fn else None}
    localized=[iou(r['humanLabels']['regionBox'],r['modelPredictions']['regionBox']) for r in labeled if 'regionBox' in r['humanLabels'] and 'regionBox' in r['modelPredictions']]
    poor=[r for r in classified if r.get('lightingCondition') in ('dim','asymmetric','clipped')]
    groups=defaultdict(list)
    for r in classified:
        if r.get('comparisonPairId') and r['humanLabels'].get('stablePair'):groups[r['comparisonPairId']].append(r['modelPredictions']['classification'])
    stability=[len(set(values))==1 for values in groups.values() if len(values)>1]
    changes=[r['humanLabels']['changeDirection']==r['modelPredictions'].get('changeDirection') for r in labeled if 'changeDirection' in r['humanLabels'] and 'changeDirection' in r['modelPredictions']]
    return {'status':'EVALUATED','real_labeled_samples':len(labeled),'versions':sorted({r['modelVersion'] for r in labeled}),
            'classification_n':len(classified),'classification_agreement':sum(label==pred for label,pred in pairs.elements())/len(classified) if classified else None,
            'per_class':per_class,'region_iou_n':len(localized),'region_iou_mean':sum(localized)/len(localized) if localized else None,
            'poor_lighting_n':len(poor),'poor_lighting_error_rate':sum(r['humanLabels']['classification']!=r['modelPredictions']['classification'] for r in poor)/len(poor) if poor else None,
            'stable_pair_n':len(stability),'prediction_stability':sum(stability)/len(stability) if stability else None,
            'change_pair_n':len(changes),'before_after_agreement':sum(changes)/len(changes) if changes else None}
def validate_rows(rows):
    import jsonschema
    schema=json.loads((Path(__file__).resolve().parents[1]/'docs/MAKEUP_EVALUATION_SCHEMA.json').read_text(encoding='utf-8'))
    for row in rows:jsonschema.validate(row,schema)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('samples',type=Path);parser.add_argument('--output',type=Path);args=parser.parse_args()
    rows=[json.loads(line,parse_constant=lambda value:(_ for _ in ()).throw(ValueError('Non-finite JSON number'))) for line in args.samples.read_text(encoding='utf-8').splitlines() if line.strip()]
    # Do not silently accept malformed schema/consent labels.
    validate_rows(rows)
    report=json.dumps(evaluate(rows),ensure_ascii=False,indent=2)
    if args.output:args.output.write_text(report,encoding='utf-8')
    print(report)
if __name__=='__main__':main()
