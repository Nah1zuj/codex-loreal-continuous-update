from scripts.evaluate_makeup_vision import evaluate,iou

def test_no_real_authorized_labels_means_no_accuracy():
    assert evaluate([])['status']=='NOT_EVALUATED'
    assert evaluate([{'sourceType':'synthetic','consentStatus':'granted','allowedUse':['evaluate'],'humanLabels':{'classification':'a'}}])['status']=='NOT_EVALUATED'

def test_metric_arithmetic_fixture_not_a_model_benchmark():
    rows=[{'sampleId':str(i),'sourceType':'real_labeled','consentStatus':'granted','allowedUse':['evaluate'],'modelVersion':'unit-test-only',
           'lightingCondition':'dim','humanLabels':{'classification':'a'},'modelPredictions':{'classification':pred}} for i,pred in enumerate(['a','b'])]
    report=evaluate(rows);assert report['classification_agreement']==.5
    assert report['per_class']['b']['false_positive']==1
    assert report['poor_lighting_error_rate']==.5
    assert iou([0,0,2,2],[0,0,2,2])==1

def test_calibration_filters_nonfinite_and_mixed_versions_without_activation():
    from scripts.calibrate_makeup_thresholds import calibrate
    row={'sourceType':'real_labeled','consentStatus':'granted','allowedUse':['calibrate'],'makeupRegion':'blush','modelVersion':'unit-only','humanLabels':{'classification':'approximately_balanced'},'modelPredictions':{'features':{'left_minus_right_lab_a':float('nan')}}}
    assert calibrate([row]*30)['records']==0
    row['modelPredictions']['features']['left_minus_right_lab_a']=0
    other={**row,'modelVersion':'other-unit-only'}
    report=calibrate([row]*29+[other]);assert report['status']=='NOT_CALIBRATED' and report['activated'] is False
