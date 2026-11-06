export type Page='home'|'speak'|'session'|'camera'|'memory'|'dot'|'pair'|'story'|'demo'|'voice'|'explore'|'full-look'|'devices'|'mirror'
export const pagePaths:Record<Page,string>={home:'/',speak:'/speak',session:'/thread',camera:'/echo',memory:'/imprint',dot:'/dot',pair:'/pair',story:'/story',demo:'/demo',voice:'/voice',explore:'/explore','full-look':'/full-look',devices:'/devices',mirror:'/mirror'}
export function pageFromPath(path:string):Page{if(path==='/video')return 'explore';return (Object.entries(pagePaths).find(([,url])=>url===path)?.[0] as Page)??'home'}
export function resolvePage(key:string):Page{return ({thread:'session',echo:'camera',imprint:'memory'} as Record<string,Page>)[key]??key as Page}
export function pageUrl(page:Page,demo:boolean){return pagePaths[page]+(demo?'?demo=true':'')}
export function initialPage(path:string,search:string):Page{return path==='/'&&new URLSearchParams(search).get('demo')==='true'?'demo':pageFromPath(path)}
