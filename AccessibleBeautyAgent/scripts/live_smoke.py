"""Verify running HTTP services with disposable test data and cleanup."""
import uuid
import httpx

def main():
    user='smoke_'+uuid.uuid4().hex
    with httpx.Client(base_url='http://127.0.0.1:8000',timeout=30) as c:
        def post(path,data,status=200):
            r=c.post('/api'+path,json=data)
            assert r.status_code==status,(path,r.status_code,r.text)
            return r.json()
        h=c.get('/api/health').json()
        assert h['status']=='ok' and h['provider_mode']=='mock'
        r=post('/chat',{'user_id':user,'message':'今晚有一个正式 dinner，我想精致一点但别太成熟'})
        assert r['session']['selected_look']=='soft_formal'
        sid=r['session']['session_id']
        rag=post('/rag/search',{'query':'dinner blush','filters':{'scene':'dinner'}})
        assert rag['results'] and all('dinner' in x['metadata']['scene'] for x in rag['results'])
        post('/chat',{'session_id':sid,'message':'check this'})
        post('/chat',{'session_id':sid,'action':'camera_consent','consent':True})
        vision=post('/vision/check',{'session_id':sid,'task':'blush_presence','demo':True,'mock_status':'BOTH'})
        assert vision['visual']['status']=='BOTH' and vision['visual']['simulated']
        continued=post('/chat',{'session_id':sid,'message':'next'})
        assert continued['session']['routine_started'] and continued['session']['routine_step']==0
        post('/memory',{'user_id':user,'candidate':{'feedback':'Disposable live test'},'explicit_consent':False},403)
        assert c.get('/api/profile/'+user).json()['episodes']==[]
        saved=post('/memory',{'user_id':user,'candidate':{'feedback':'Disposable live test','preferred_saturation':'low'},'explicit_consent':True})
        assert c.get('/api/profile/'+user).json()['profile']['preferred_saturation']=='low'
        response=c.delete('/api/memory/'+saved['memory_id'],params={'user_id':user,'explicit_consent':'true'})
        assert response.status_code==200
        assert c.get('/api/profile/'+user).json()['episodes']==[]
        assert httpx.get('http://127.0.0.1:5173').status_code==200
        post('/chat',{'session_id':sid,'message':'stop'})
    print('LIVE PASS: backend health, frontend HTTP, dinner Look, filtered RAG, structured mock vision, consent refusal, persistence and deletion.')

if __name__=='__main__':main()
