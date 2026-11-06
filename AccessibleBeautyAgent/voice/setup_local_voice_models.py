"""Download official model assets; extract data only, never run archive code."""
from pathlib import Path
import hashlib,json,tarfile,urllib.request,os,ssl
import certifi
ROOT=Path(__file__).resolve().parent
SOURCES={
 'kws-bilingual': 'https://github.com/k2-fsa/sherpa-onnx/releases/download/kws-models/sherpa-onnx-kws-zipformer-zh-en-3M-2025-12-20.tar.bz2',
 'asr': 'https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2024-07-17.tar.bz2',
}
REQUIRED={
 'kws-bilingual':('tokens.txt','en.phone','encoder-epoch-13-avg-2-chunk-8-left-64.int8.onnx','decoder-epoch-13-avg-2-chunk-8-left-64.onnx','joiner-epoch-13-avg-2-chunk-8-left-64.int8.onnx'),
 'asr':('model.int8.onnx','tokens.txt'),
}
def ready():return all((ROOT/'models'/key/name).is_file() for key,names in REQUIRED.items() for name in names)
def download():
 records=[]
 for key,url in SOURCES.items():
  target=ROOT/'models'/key;target.mkdir(parents=True,exist_ok=True)
  if not all((target/name).is_file() for name in REQUIRED[key]):
   archive=ROOT/(key+'.tar.bz2')
   print('Downloading '+key,flush=True)
   with urllib.request.urlopen(url,context=ssl.create_default_context(cafile=certifi.where()),timeout=60) as response, archive.open('wb') as output:
    while chunk:=response.read(1024*1024): output.write(chunk)
   with tarfile.open(archive) as tf:
    for member in tf.getmembers():
     name=Path(member.name)
     if not member.isfile() or name.name not in (*REQUIRED[key],'LICENSE','README.md'):continue
     relative=Path(*name.parts[1:])
     if relative.is_absolute() or '..' in relative.parts:raise ValueError('Unsafe archive path')
     dest=target/relative;dest.parent.mkdir(parents=True,exist_ok=True)
     with tf.extractfile(member) as src, dest.open('wb') as dst:dst.write(src.read())
   archive.unlink()
  for file in sorted(target.rglob('*')):
   if file.is_file() and file.parent==target and file.name in (*REQUIRED[key],'LICENSE','README.md'):records.append({'file':str(file.relative_to(ROOT)),'source':url,'bytes':file.stat().st_size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
 (ROOT/'MODEL-SOURCES.json').write_text(json.dumps({'code':'https://github.com/k2-fsa/sherpa-onnx','assets':records},ensure_ascii=False,indent=2)+'\n')
 print('Official local speech models ready',flush=True)
if __name__=='__main__':download()
