import json
from pathlib import Path
from app.config import ROOT

DEFAULTS={
 'scenes':['daily','dinner','presentation','social'],
 'impressions':['natural','fresh','polished','slightly_present','controlled','warm','approachable'],
 'makeup_areas':['base','blush','lip','eye','brush','final'],
 'intensity_levels':['very_low','low','light','medium_low','light_medium','medium','medium_high','high','minimal'],
 'finishes':['natural','light_natural','natural_polished','soft','soft_diffused','soft_satin','heavy_gloss','matte','satin','glossy'],
 'saturation_levels':['very_low','low','medium_low','medium','medium_high','high'],
 'reference_status':['RAW','DRAFT','AI_GENERATED','HUMAN_VERIFIED','REJECTED','DEPRECATED'],
 'placements':['upper_cheek','cheek'],
 'accessibility_categories':['voice_instruction','spatial_instruction','confirmation','camera_consent','memory_consent','error_recovery','progressive_disclosure','user_control'],
}
ALIASES={'dinner':['dinner','晚宴','晚餐','正式','约会'],'presentation':['presentation','演讲','汇报'],'daily':['daily','日常','上班','清爽'],'social':['social','聚会','社交','朋友']}

class Vocabulary:
    def __init__(self,directory=None):
        self.directory=Path(directory or ROOT/'data/config')
        self.values={};self.scene_aliases=ALIASES.copy()
        for name,values in DEFAULTS.items():
            path=self.directory/f'{name}.json'
            raw=json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else values
            self.values[name]=raw.get('values',values) if isinstance(raw,dict) else raw
            if name=='scenes' and isinstance(raw,dict):self.scene_aliases.update(raw.get('aliases',{}))
    def parse_query(self,query):
        text=query.lower()
        for scene in self.values['scenes']:
            if any(x.lower() in text for x in self.scene_aliases.get(scene,[scene])):return {'scene':scene}
        return {}
