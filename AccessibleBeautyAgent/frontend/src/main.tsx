import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './style.css'
import './styles/traceTokens.css'
import './styles/trace.css'
import './styles/companion.css'
import './styles/story.css'
import './styles/sculpture.css'
import './styles/reference.css'
import './styles/fidelity.css'
import './styles/appleAtmosphere.css'
import './styles/storyLayout.css'
import './styles/homeComposition.css'
import './styles/referenceCharacter.css'
import './styles/iterationV2.css'
import '@fontsource/noto-serif-sc/400.css'
import '@fontsource/cormorant-garamond/latin-400.css'
import {LocaleProvider} from './content/Locale'
const AdminApp=React.lazy(()=>import('./admin/AdminApp'))
const root=ReactDOM.createRoot(document.getElementById('root')!)
root.render(<p role="status">正在进入 TRACE…</p>)
fetch('/api/identity',{credentials:'same-origin'}).then(response=>{if(!response.ok)throw new Error('identity unavailable');root.render(<React.StrictMode>{window.location.pathname.startsWith('/admin')?<React.Suspense fallback={<p role="status">加载研究工作台…</p>}><AdminApp/></React.Suspense>:<LocaleProvider><App/></LocaleProvider>}</React.StrictMode>)}).catch(()=>root.render(<p role="alert">私人会话暂时无法开启，请刷新重试。 Private session unavailable. Please reload.</p>))
