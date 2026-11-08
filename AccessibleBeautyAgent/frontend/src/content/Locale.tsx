import {guidanceText} from './guidance'
import {createContext,useContext,useState,type ReactNode} from 'react'
import {productCopy,type Locale} from './traceBrand'
export type LanguageDisplay='chinese'|'bilingual'|'english'
const Context=createContext<{locale:Locale;setLocale:(locale:Locale)=>void;display:LanguageDisplay;setDisplay:(mode:LanguageDisplay)=>void}>({locale:'zh-CN',setLocale:()=>{},display:'bilingual',setDisplay:()=>{}})
export function bilingual(zh:string,en:string,locale:Locale='zh-CN'){return locale==='zh-CN'?zh:en}
export function LocaleProvider({children,initialLocale='zh-CN'}:{children:ReactNode;initialLocale?:Locale}){const [locale,changeLocale]=useState<Locale>(initialLocale);const [display,changeDisplay]=useState<LanguageDisplay>(initialLocale==='en'?'english':'bilingual');const setLocale=(next:Locale)=>{changeLocale(next);changeDisplay(next==='en'?'english':'chinese')};const setDisplay=(next:LanguageDisplay)=>{changeDisplay(next);changeLocale(next==='english'?'en':'zh-CN')};return <Context.Provider value={{locale,setLocale,display,setDisplay}}>{children}</Context.Provider>}
export function useTrace(){const value=useContext(Context);return {...value,c:productCopy[value.locale],t:(zh:string,en:string)=>bilingual(zh,en,value.locale),d:(text:string)=>guidanceText(text,value.locale)}}
