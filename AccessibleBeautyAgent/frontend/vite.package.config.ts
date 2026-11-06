import baseConfig from './vite.config'
import {defineConfig} from 'vite'
export default defineConfig({...baseConfig,server:{...baseConfig.server,host:'127.0.0.1',port:5180,strictPort:true,proxy:{'/api':'http://127.0.0.1:8012','/local-voice':{target:'http://127.0.0.1:8013',ws:true,rewrite:path=>path.replace(/^\/local-voice/,'/voice')}}}})
