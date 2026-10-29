from test_acceptance import client,chat

def test_continue_after_preliminary_check_starts_routine(client):
    r=chat(client,'dinner');sid=r['session']['session_id']
    chat(client,'check this',sid)
    chat(client,'',sid,action='camera_consent',consent=True)
    checked=client.post('/api/vision/check',json={'session_id':sid,'demo':True,'mock_status':'BOTH','images':[]})
    assert checked.status_code==200
    assert checked.json()['session']['routine_started'] is False
    r=chat(client,'next',sid)
    assert r['session']['routine_started'] is True
    assert r['session']['routine_step']==0
    assert r['session']['stage']=='GUIDE'
    assert r['step']['step_id']=='base'
