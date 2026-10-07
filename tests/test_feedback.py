from backend.feedback import enrich_reps


def test_fault_explanation_uses_measured_peak_without_changing_verdict():
    rep={'start_s':1,'end_s':3,'bottom_s':2,'max_thigh_angle':85,'verdict':'improper','fault_codes':['shin_over_toe']}
    samples=[{'t':t,'validity':'valid','shin_angle':angle,'hip_angle':30,'feedback_codes':[]} for t,angle in [(0,75),(1,40),(2,52),(3,45)]]
    enrich_reps([rep],samples,'beginner')
    detail=rep['feedback_details'][0]
    assert detail['measured']==52 and detail['threshold']==45 and detail['time_s']==2
    assert rep['verdict']=='improper' and rep['fault_codes']==['shin_over_toe']


def test_torso_cue_is_advisory_and_missing_trigger_not_invented():
    rep={'start_s':1,'end_s':3,'bottom_s':2,'max_thigh_angle':85,'verdict':'improper','fault_codes':['shin_over_toe']}
    samples=[{'t':2,'validity':'valid','shin_angle':20,'hip_angle':55,'feedback_codes':['bend_backward']}]
    enrich_reps([rep],samples,'pro')
    fault,advice=rep['feedback_details']
    assert fault['measured'] is None and fault['threshold']==30
    assert not advice['affects_verdict'] and advice['measured']==55


def test_skipped_bottom_band_is_not_described_as_insufficient_depth():
    rep={'start_s':1,'end_s':3,'bottom_s':2,'max_thigh_angle':100,'verdict':'improper','fault_codes':['shallow','too_deep']}
    samples=[{'t':t,'validity':'valid','thigh_angle':angle,'hip_angle':30,'feedback_codes':[]} for t,angle in [(1,50),(2,100),(3,10)]]
    enrich_reps([rep],samples,'beginner')
    phase,excess=rep['feedback_details']
    assert 'tracking/sampling' in phase['explanation']
    assert phase['measured']==100 and excess['measured']==100
    assert rep['verdict']=='improper'
