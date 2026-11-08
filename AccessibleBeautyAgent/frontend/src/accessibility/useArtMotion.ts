import {useEffect} from 'react'
import gsap from 'gsap'
/** Keep meaningful text intact; animate only its container and undo every style. */
export function useArtMotion(page:string,enabled:boolean){useEffect(()=>{const scope=document.querySelector('main');if(!scope||!window.matchMedia)return;const media=gsap.matchMedia();media.add('(prefers-reduced-motion: no-preference)',()=>{if(!enabled)return;const context=gsap.context(()=>{const headings=scope.querySelectorAll('h1'),entries=scope.querySelectorAll('.entry-options button');if(headings.length)gsap.from(headings,{y:12,opacity:.6,duration:.8,ease:'power2.out'});if(entries.length)gsap.from(entries,{y:9,opacity:.7,stagger:.08,duration:.7,ease:'power2.out'})},scope);return()=>context.revert()});return()=>media.revert()},[page,enabled])}
