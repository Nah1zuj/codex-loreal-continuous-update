import {Component,lazy,Suspense,useEffect,useRef,useState,type ReactNode} from 'react'
import type {CallSnapshot} from '../realtime/callController'
const Scene=lazy(()=>import('./SculptureScene').catch(()=>({default:StaticSculpture})))
class VisualBoundary extends Component<{children:ReactNode},{failed:boolean}>{state={failed:false};static getDerivedStateFromError(){return {failed:true}}render(){return this.state.failed?null:this.props.children}}
export type VisualVariant='hero'|'voice'|'makeup'|'full-look'|'memory'|'apple'|'wireframe'|'sculpture'
export interface SceneProps {variant:VisualVariant;showHuman?:boolean;showPortrait?:boolean;appleArtwork?:boolean;composition?:'centered-home';enabled?:boolean;state?:CallSnapshot['state'];region?:string;modelUrl?:string;settled?:boolean;audioReactive?:boolean;onAudioError?:()=>void;view?:'front'|'three-quarter'|'left'|'right'|'up'|'down'}
/** A scene always belongs to this positioned page/section, never to the viewport. */
export function SectionBackground(props:SceneProps){
 const host=useRef<HTMLDivElement>(null),[visible,setVisible]=useState(false)
 const portrait=props.showPortrait!==false&&props.variant!=='apple',particles=true
 useEffect(()=>{if(typeof IntersectionObserver==='undefined'){setVisible(true);return}const observer=new IntersectionObserver(entries=>setVisible(entries.some(e=>e.isIntersecting)),{rootMargin:'80px'});if(host.current)observer.observe(host.current);return()=>observer.disconnect()},[])
 return <div ref={host} className={'section-background scene-'+props.variant+' reference-character-scene'} aria-hidden="true" data-character={portrait?"mesh-preview":"none"} data-motion={props.enabled===false?'off':'on'}>
  <div className="section-light"/>
  {visible&&particles?<VisualBoundary key={props.variant}><Suspense fallback={null}><Scene {...props} showHuman={false} appleArtwork={props.variant==='hero'}/></Suspense></VisualBoundary>:null}
  {props.variant==='hero'?<img className="reference-apple-art" src="/visuals/apple-reference.png" alt="" width="1254" height="1254" decoding="async" draggable={false}/>:null}
  {portrait?<img className="reference-character" src="/visuals/mesh-portrait-preview.png" alt="" width="150" height="220" decoding="async" draggable={false}/>:null}
 </div>
}
export function StaticSculpture(){return <img className="static-sculpture" src="/visuals/mesh-portrait-preview.png" alt="" width="150" height="220"/>}
