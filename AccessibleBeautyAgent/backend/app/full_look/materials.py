"""Inspectable category knowledge; never derive fiber composition from pixels."""
import json
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Literal

class MaterialKnowledge(BaseModel):
    material_id: str
    name_zh: str
    name_en: str
    kind: Literal['fiber','structure']
    texture_description: str
    weight_drape: str
    breathability_notes: str
    care_notes: str
    visual_style_tags: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    verification_status: Literal['DRAFT','HUMAN_VERIFIED'] = 'DRAFT'

class MaterialService:
    def __init__(self,path=None):
        path=path or Path(__file__).resolve().parents[3]/'data/materials/materials.json'
        self.rows=[MaterialKnowledge.model_validate(x).model_dump() for x in json.loads(path.read_text(encoding='utf-8'))]
        self.by_id={x['material_id']:x for x in self.rows}
    def explain(self,ids):
        if any(x not in self.by_id for x in ids):raise KeyError('Material not found')
        rows=[self.by_id[x] for x in dict.fromkeys(ids)]
        parts=['以下为有来源的类别知识候选，仍待人工审核；不是对你衣服成分的判断。']
        for r in rows:
            parts.append(f"{r['name_zh']}（{r['name_en']}）是{'纤维类别' if r['kind']=='fiber' else '织造结构，不等于特定纤维'}。{r['texture_description']} {r['weight_drape']} {r['breathability_notes']} {r['care_notes']}")
        parts.append('具体纤维成分以衣服吊牌、官方信息或你的明确确认作为依据；照片外观不能确定成分。')
        return {'results':rows,'message':'\n'.join(parts)}

