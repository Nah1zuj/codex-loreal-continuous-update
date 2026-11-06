import {it,expect} from 'vitest'
import {renderToStaticMarkup} from 'react-dom/server'
import {LocalFrameOverlay} from './LocalFrameOverlay'
it('draws only actual validated native bounds on the corresponding captured frame',()=>{
 const props={image:'fixture',capturedAt:1,observation:{method:'mediapipe_masked_lab',simulated:false,geometry:{face_detected:true,face_count:1,landmark_count:478,face_bounds:[.2,.1,.5,.7]}}}
 const html=renderToStaticMarkup(<LocalFrameOverlay {...props}/>)
 expect(html).toContain('data-face-overlay="captured-frame"')
 expect(html).toContain('viewBox="0 0 1 1"')
 expect(html).toContain('not live tracking')
 for(const observation of [{...props.observation,simulated:true},{...props.observation,geometry:{...props.observation.geometry,face_bounds:[.9,.1,.5,.7]}},{...props.observation,geometry:{...props.observation.geometry,face_count:0}}])expect(renderToStaticMarkup(<LocalFrameOverlay {...props} observation={observation}/>)).toBe('')
})
