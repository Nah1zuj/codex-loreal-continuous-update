import {useEffect,useState} from 'react'
import {useTrace} from '../content/Locale'
export function ReadingControls(){
 const {t}=useTrace();const [large,setLarge]=useState(false),[contrast,setContrast]=useState(false)
 useEffect(()=>{
  document.documentElement.dataset.traceTextSize=large?'large':'standard'
  document.documentElement.dataset.traceContrast=contrast?'high':'standard'
  return()=>{delete document.documentElement.dataset.traceTextSize;delete document.documentElement.dataset.traceContrast}
 },[large,contrast])
 return <details className="reading-controls"><summary>{t('阅读设置','Reading settings')}</summary><button aria-pressed={large} onClick={()=>setLarge(value=>!value)}>{large?t('恢复标准字号','Standard text size'):t('放大文字','Larger text')}</button><button aria-pressed={contrast} onClick={()=>setContrast(value=>!value)}>{contrast?t('恢复柔光配色','Soft palette'):t('提高文字对比度','Higher contrast')}</button></details>
}
