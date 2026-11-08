export type Stage = 'INIT'|'ONBOARDING'|'INTENT'|'CLARIFY'|'LOOK_SELECTED'|'GUIDE'|'CHECK_REQUESTED'|'CAMERA_CONSENT'|'VISION_GATE'|'VISION_CHECK'|'VERIFY'|'FEEDBACK'|'MEMORY_CONSENT'|'COMPLETE'
export interface Step {step_id:string;name:string;instruction:string;instruction_slow:string;instruction_repeat:string;explanation_why:string;visual_check_required:boolean;visual_task:'blush_presence'|'lip_presence'|null}
export interface Session {current_step?:Step|null;last_response?:string;todays_look?:FullLook;experience_mode?:ExperienceMode|null;session_id:string;user_id:string;stage:Stage;scene:string|null;desired_impression:string[];avoid:string[];selected_look:string|null;selected_products:Array<{product_id:string;description:string}>;routine_id:string|null;routine_step:number;routine_total_steps:number;routine_started:boolean;camera_consent:boolean;memory_consent:boolean;visual_state:Visual|null;confidence:number;last_tool_call:unknown;rag_documents:unknown[];memory_candidate:Record<string,unknown>|null;memory_candidate_id?:string|null;memory_candidate_version?:string|null;stage_history:string[]}
export interface Reply {canonical?:{message:string;session:Session;step:Step|null};message:string;session:Session;step:Step|null;mode?:string}
export interface MakeupPlan {id:string;revision:number;status:'draft'|'active'|'completed';active_index:number;workflow:string;steps:Array<{id:string;title:string;status:string}>}
export interface Session {makeup_plan?:MakeupPlan|null;course_unavailable?:boolean}
export interface Visual {task:string;status:string;confidence:number;simulated:boolean;frame_results?:unknown[]}
export interface VisionReply extends Reply {visual:Visual|null;gate:Record<string,unknown>}
export interface MemoryEpisode {memory_id:string;version?:string;feedback:string;context:string;timestamp:string;preferred_finish?:string[];preferred_saturation?:string|null;avoid?:string[]}
export interface Profile {user_id:string;profile:{preferred_finish:string[];preferred_saturation:string|null;avoid:string[]};episodes:MemoryEpisode[]}
export interface Health {status:string;provider_mode:string;providers:{language:string;vision:string;embedding:string;voice:string};developer_mode:boolean;remote_ready:boolean;reading_provider?:string;allow_remote_ai?:boolean}

export type ExperienceMode='voice'|'visual'|'text'
export type CameraState='off'|'requesting'|'live'|'denied'|'unavailable'|'error'
export type LookDomain='skincare'|'makeup'|'hair'|'outfit'|'accessories'|'fragrance'
export interface LookSection {selected_suggestion_id?:string|null;facts?:string[];unknowns?:string[];state:'proposed'|'confirmed'|'skipped';optional:boolean;suggestions:Array<{id:string;display_name_zh:string;display_name_en:string;reason:string;source_refs:string[];verified_status:string;user_override:boolean;optional:boolean}>;materials:string[];look_id?:string|null;routine_id?:string|null}
export interface FullLook {plan_id:string;session_id:string;scene:string;desired_impression:string[];review_status:string;version:number;sections:Record<LookDomain,LookSection>;source_refs:string[];uncertainties:string[];user_confirmed_sections:string[]}
export interface Material {material_id:string;name_zh:string;name_en:string;kind:string;texture_description:string;weight_drape:string;breathability_notes:string;care_notes:string;visual_style_tags:string[];source_refs:string[];verification_status:string}
