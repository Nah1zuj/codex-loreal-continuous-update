"""Offline audio decoding. Quiet mode never calls ordinary ASR before a wake candidate."""
from pathlib import Path
from collections import deque
import os,threading,re
import numpy as np
import sherpa_onnx

ROOT=Path(__file__).resolve().parent
WAKE=('重新启动语音交流功能','重新开启语音功能','resume voice')
PAUSE=('请终止对话','暂停语音','暂停回应','停止语音播报','停止','pause replies','pause voice','stop speaking','stop')
CONTROL=WAKE+PAUSE+('开始','结束','可以开始','下一步','上一步','再说一次','帮助','跳过','结束本次装扮','next','previous','repeat','help','skip','finish this look')
PUNCT=re.compile(r'[\s，,。.!！?？：:；;“”"、]+')

def clean(text):return PUNCT.sub('',text).strip().lower()
def wake_tail(text):
    value=clean(text)
    for phrase in WAKE:
        if value.startswith(clean(phrase)) and not any(term in value[len(clean(phrase)):] for term in ('是什么意思','这个词','这句话')):return phrase,value[len(clean(phrase)):]
    return None
def pause_command(text):
    value=clean(text)
    return value in {clean(phrase) for phrase in PAUSE} or value.lower() in {'stop','pausereplies'}

class Models:
    def __init__(self):
        k=ROOT/'models/kws-bilingual';a=ROOT/'models/asr'
        self.lock=threading.Lock()
        self.kws={}
        directory=Path(os.getenv('TRACE_WORK_DIR',ROOT.parent/'work'))
        directory.mkdir(parents=True,exist_ok=True)
        for mode,phrases in [('quiet',WAKE),('active',CONTROL)]:
            tokens=sherpa_onnx.text2token([phrase.upper() if phrase.isascii() else phrase for phrase in phrases],tokens=str(k/'tokens.txt'),tokens_type='phone+ppinyin',lexicon=str(k/'en.phone'))
            if len(tokens)!=len(phrases):raise RuntimeError('Keyword encoding incomplete')
            keywords=directory/(mode+'-keywords.txt')
            keywords.write_text('\n'.join(' '.join(row)+' :2.0 #0.25 @'+phrase.replace(' ','_') for row,phrase in zip(tokens,phrases))+'\n')
            self.kws[mode]=sherpa_onnx.KeywordSpotter(tokens=str(k/'tokens.txt'),encoder=str(k/'encoder-epoch-13-avg-2-chunk-8-left-64.int8.onnx'),decoder=str(k/'decoder-epoch-13-avg-2-chunk-8-left-64.onnx'),joiner=str(k/'joiner-epoch-13-avg-2-chunk-8-left-64.int8.onnx'),keywords_file=str(keywords),num_threads=2)
        self.asr=sherpa_onnx.OfflineRecognizer.from_sense_voice(model=str(a/'model.int8.onnx'),tokens=str(a/'tokens.txt'),num_threads=2,language='auto',use_itn=True)
    def transcribe(self,samples):
        with self.lock:
            stream=self.asr.create_stream();stream.accept_waveform(16000,samples);self.asr.decode_stream(stream)
            return stream.result.text.strip()

class AudioSession:
    MAX_SAMPLES=16000*12
    def __init__(self,models,*,defer_transcription=False):
        self.defer_transcription=defer_transcription
        self.models=models;self.mode='quiet';self.epoch=0
        self.metrics={'pcm_frames':0,'asr_utterances':0,'wake_candidates':0,'emitted_utterances':0,'audio_saved':False,'remote_asr_requests':0}
        self.reset()
    def reset(self):
        self.stream=self.models.kws['quiet' if self.mode=='quiet' else 'active'].create_stream()
        self.frames=deque();self.size=0;self.silence=0;self.voiced=False;self.candidate=''
        self.capturing=False;self.capture_frames=[];self.capture_size=0;self.capture_ended=False;self.manual_capture=False
    def configure(self,mode,epoch):
        if mode not in {'active','quiet','speaking','bounded'} or not isinstance(epoch,int) or epoch<self.epoch:raise ValueError('Invalid voice mode')
        self.mode=mode;self.epoch=epoch;self.reset()
    def feed(self,raw):
        if not raw or len(raw)%2 or len(raw)>64000:raise ValueError('Invalid PCM frame')
        samples=np.frombuffer(raw,dtype='<i2').astype(np.float32)/32768
        self.metrics['pcm_frames']+=1
        rms=float(np.sqrt(np.mean(samples*samples)))
        self.voiced=self.voiced or rms>.007
        self.silence=0 if rms>.007 else self.silence+len(samples)
        self.frames.append(samples);self.size+=len(samples)
        while self.size>self.MAX_SAMPLES and self.frames:self.size-=len(self.frames.popleft())
        spotter=self.models.kws['quiet' if self.mode=='quiet' else 'active']
        self.stream.accept_waveform(16000,samples)
        with self.models.lock:
            while spotter.is_ready(self.stream):
                spotter.decode_stream(self.stream)
                result=spotter.get_result(self.stream)
                if result:
                    self.candidate=result;spotter.reset_stream(self.stream)
                    if result.replace('_',' ') in WAKE:self.metrics['wake_candidates']+=1
        if self.mode=='bounded':return self.feed_bounded(samples)
        if self.voiced and (self.silence>=8320 or self.size>=self.MAX_SAMPLES):
            eligible=self.mode=='active' or bool(self.candidate)
            data=np.concatenate(list(self.frames)) if eligible else None
            mode,epoch=self.mode,self.epoch
            self.reset()
            if data is None:return None
            self.metrics['asr_utterances']+=1
            text=self.models.transcribe(data)
            if not text:return None
            wake=wake_tail(text)
            if mode=='quiet' and not wake:return None
            if mode=='speaking' and not (wake or pause_command(text) or clean(text) in {clean(phrase) for phrase in CONTROL}):return None
            self.metrics['emitted_utterances']+=1
            return {'type':'transcript','text':text,'epoch':epoch,'kind':'wake' if wake else 'speech'}
        if not self.voiced and self.size>4800:
            while self.size>3200:self.size-=len(self.frames.popleft())
        return None
    def begin_capture(self):
        if self.mode!='bounded' or self.capturing:return None
        self.reset();self.capturing=True;self.manual_capture=True
        return {'type':'capture','recording':True,'epoch':self.epoch}
    def finish_capture(self,explicit=False):
        if self.mode!='bounded' or not self.capturing:return None
        data=np.concatenate(self.capture_frames) if self.capture_frames else None
        epoch,manual=self.epoch,self.manual_capture
        self.reset()
        if data is None or len(data)<1600:return {'type':'capture','recording':False,'discarded':True,'reason':'no_audio','epoch':epoch}
        self.metrics['asr_utterances']+=1
        text=self.models.transcribe(data).strip()
        if manual:
            if text.startswith('开始'):text=text[2:]
            end=text.find('结束');body=text[:end] if end>=0 else text
        else:
            begin=text.find('开始');end=text.find('结束',begin+2) if begin>=0 else -1
            body=text[begin+2:end] if end>=0 else text[begin+2:] if explicit and begin>=0 else ''
        body=body.strip(' ，,。.!！?？：:；;')
        if not body:return {'type':'capture','recording':False,'discarded':True,'reason':'unrecognized','epoch':epoch}
        self.metrics['emitted_utterances']+=1
        return {'type':'transcript','text':body,'epoch':epoch,'kind':'bounded'}
    def feed_bounded(self,samples):
        # Neither silence nor unrelated speech submits audio without an explicit boundary.
        candidate=self.candidate.replace('_',' ');self.candidate=''
        if not self.capturing:
            if candidate!='开始':
                while self.size>32000 and self.frames:self.size-=len(self.frames.popleft())
                return None
            self.capturing=True
            self.capture_frames=list(self.frames);self.capture_size=sum(len(frame) for frame in self.capture_frames)
            return {'type':'capture','recording':True,'epoch':self.epoch}
        self.capture_frames.append(samples);self.capture_size+=len(samples)
        if candidate=='结束':self.capture_ended=True
        if self.capture_size>16000*120:
            epoch=self.epoch;self.reset()
            return {'type':'capture','recording':False,'discarded':True,'reason':'duration_limit','epoch':epoch}
        if self.capture_ended and self.silence>=8320:
            if self.defer_transcription:return {'type':'transcribing','epoch':self.epoch}
            return self.finish_capture()
        return None
    def dispose(self):self.capture_frames.clear();self.capturing=False;self.frames.clear();self.size=0;self.stream=None;self.candidate=''
