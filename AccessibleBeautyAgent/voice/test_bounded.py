"""Audio gate regression checks, without microphone or network."""
import unittest,threading
import numpy as np
from engine import AudioSession
class Stream:
 def accept_waveform(self,*args):pass
class Spotter:
 def __init__(self):self.next=''
 def create_stream(self):return Stream()
 def is_ready(self,stream):return bool(self.next)
 def decode_stream(self,stream):pass
 def get_result(self,stream):result=self.next;self.next='';return result
 def reset_stream(self,stream):pass
class Models:
 def __init__(self):
  self.lock=threading.Lock();self.spotter=Spotter();self.kws={'quiet':self.spotter,'active':self.spotter};self.calls=[];self.text='闲聊。开始，我想要自然的腮红。结束。闲聊'
 def transcribe(self,samples):self.calls.append(samples);return self.text
class BoundedTests(unittest.TestCase):
 def setUp(self):self.m=Models();self.s=AudioSession(self.m);self.s.configure('bounded',1)
 def feed(self,keyword='',silent=False):
  self.m.spotter.next=keyword
  return self.s.feed((np.zeros(9600,dtype='<i2') if silent else np.full(9600,1000,dtype='<i2')).tobytes())
 def test_only_between_words_and_exactly_once(self):
  for _ in range(8):self.assertIsNone(self.feed())
  self.assertEqual(self.m.calls,[]);self.assertTrue(self.feed('开始')['recording'])
  for _ in range(5):self.feed();self.feed(silent=True)
  self.assertEqual(self.m.calls,[]);self.feed('结束');event=self.feed(silent=True)
  self.assertEqual(event['text'],'我想要自然的腮红');self.assertEqual(len(self.m.calls),1)
  for _ in range(8):self.feed(silent=True)
  self.assertEqual(len(self.m.calls),1)
 def test_end_without_start_is_ignored(self):
  self.feed('结束');self.feed(silent=True);self.assertEqual(self.m.calls,[])
 def test_pause_or_route_switch_discards_pending_audio(self):
  self.feed('开始');self.feed();self.s.configure('quiet',2);self.s.configure('bounded',3)
  self.feed('结束');self.feed(silent=True);self.assertEqual(self.m.calls,[])
 def test_empty_or_unconfirmed_keywords_do_not_emit(self):
  for text in ['开始，结束','我没有说起止词']:
   self.m.text=text;self.feed('开始');self.feed('结束');event=self.feed(silent=True)
   self.assertEqual(event['type'],'capture');self.assertTrue(event['discarded'])
 def test_timeout_discards_without_transcription(self):
  self.feed('开始');self.s.capture_size=16000*120
  event=self.feed()
  self.assertTrue(event['discarded']);self.assertEqual(event['reason'],'duration_limit')
  self.assertEqual(self.m.calls,[]);self.assertEqual(self.s.capture_frames,[])
 def test_dispose_releases_capture(self):
  self.feed('开始');self.s.dispose();self.assertEqual(self.s.capture_frames,[])
 def test_button_capture_ignores_waiting_audio_and_requires_explicit_end(self):
  for _ in range(4):self.feed()
  self.m.text='我希望妆容自然一些'
  self.assertTrue(self.s.begin_capture()['recording'])
  self.feed();self.feed(silent=True);self.feed()
  self.assertEqual(self.m.calls,[])
  event=self.s.finish_capture(explicit=True)
  self.assertEqual(event['text'],'我希望妆容自然一些');self.assertEqual(len(self.m.calls),1)
  self.feed();self.assertEqual(len(self.m.calls),1)
 def test_button_can_finish_a_keyword_started_request(self):
  self.m.text='闲聊。开始，我想要自然的腮红'
  self.feed('开始');self.feed()
  self.assertEqual(self.s.finish_capture(explicit=True)['text'],'我想要自然的腮红')
 def test_button_empty_capture_and_route_change_never_submit(self):
  self.s.begin_capture();event=self.s.finish_capture(explicit=True)
  self.assertTrue(event['discarded']);self.assertEqual(self.m.calls,[])
  self.s.begin_capture();self.feed();self.s.configure('quiet',2)
  self.assertIsNone(self.s.finish_capture(explicit=True));self.assertEqual(self.m.calls,[])
if __name__=='__main__':unittest.main()
