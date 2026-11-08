"""Explicit user-provided coaching preferences and one-question clarification."""
import re

from app.agent.coaching_intents import coaching_intent
from app.knowledge.vocabulary import ALIASES
from app.schemas.makeup import PlanNeeds

LABELS = {
    'occasion': ('场合', 'occasion'),
    'aesthetic': ('妆感', '偏好', 'style', 'preference'),
    'minutes': ('时间', 'time', 'minutes'),
    'own_products': ('工具', '已有用品', 'tools', 'products'),
    'avoid': ('避讳', '避开', 'avoid'),
}
QUESTIONS = {
    'occasion': ('这次是什么场合？可以回复“场合：日常”，也可以说“开始”。',
                 'What is the occasion? Reply “occasion: daily”, or say “start”.'),
    'aesthetic': ('想要什么妆感？可以回复“妆感：自然”，也可以说“开始”。',
                  'What feeling would you like? Reply “style: natural”, or say “start”.'),
    'minutes': ('你有几分钟？可以回复“时间：15 分钟”，也可以说“开始”。',
                'How much time do you have? Reply “time: 15 minutes”, or say “start”.'),
    'own_products': ('你有哪些熟悉的工具或产品？可以回复“工具：…”，也可以说“开始”。',
                     'Which tools or products are familiar? Reply “tools: …”, or say “start”.'),
    'avoid': ('有哪些产品或步骤要避开？可以回复“避讳：…”，也可以说“开始”。',
              'Anything to avoid? Reply “avoid: …”, or say “start”.'),
}
STYLES = {
    'beginner': ('初学', 'beginner'),
    'warm': ('暖调', 'warm'),
    'professional': ('通勤', 'professional'),
    'evening': ('晚妆', 'evening'),
    'natural': ('自然', 'natural'),
}
LABEL_TO_FIELD = {label: field for field, labels in LABELS.items() for label in labels}
LABEL_PATTERN = '|'.join(map(re.escape, LABEL_TO_FIELD))
ASSIGNMENTS = re.compile(rf'(?:^|[，,。；;\n])\s*({LABEL_PATTERN})\s*[：:]\s*([^；;\n]+)', re.I)
TIME = re.compile(r'(\d{1,3}|[一二两三四五六七八九十]+)\s*(?:分钟|minutes?\b|mins?\b)', re.I)
CHINESE_NUMERALS = {name: index for index, name in enumerate('零一二三四五六七八九')}


def requested_coaching(text):
    text = text.casefold().replace('’', "'")
    if coaching_intent(text) == 'ambiguous' or re.search(r"不想|不用|不要(?:化妆|画妆)|don't want|do not want", text):
        return False
    return re.search(r'(?:想(?:要|试|画|化)|准备(?:画|化)).{0,38}妆|(?:want|would like|help me with).{0,36}\bmakeup\b', text) is not None


def minutes_from(text):
    if match := re.search(r'(\d{1,3})', text):
        return int(match.group())
    if match := re.search(r'([一二两三四五六七八九]?)(十)([一二三四五六七八九]?)', text):
        return CHINESE_NUMERALS.get(match[1].replace('两', '二'), 1) * 10 + CHINESE_NUMERALS.get(match[3], 0)
    return None


def provided_needs(text, *, initial=False, current=None):
    """Accept labeled values plus time and scene stated in an initial coaching request."""
    values = current.model_dump() if current else {}
    updates = {}
    normalized = text.strip().casefold()
    for match in ASSIGNMENTS.finditer(text):
        field = LABEL_TO_FIELD[match[1].casefold()]
        value = match[2].strip(' 。.!！')
        if not value:
            continue
        if field == 'minutes':
            minutes = minutes_from(value)
            if minutes is None or not 3 <= minutes <= 120:
                raise ValueError('时间请填写 3 到 120 分钟。 / Choose 3 to 120 minutes.')
            updates[field] = minutes
        elif field in ('own_products', 'avoid'):
            updates[field] = [] if value.casefold() in ('无', '没有', 'none', 'nothing') else [
                part.strip()[:120] for part in re.split(r'[、，,|]', value) if part.strip()
            ][:10]
        elif field == 'occasion':
            updates[field] = next((scene for scene, aliases in ALIASES.items()
                                   if value.casefold() in aliases), value[:120])
        else:
            updates[field] = value[:120]
    if initial:
        for scene, aliases in ALIASES.items():
            if any(term in normalized for term in aliases):
                updates.setdefault('occasion', scene)
                break
        if time:=TIME.search(text):
            minutes = minutes_from(time[1])
            if minutes is not None and 3 <= minutes <= 120:
                updates.setdefault('minutes', minutes)
    style_text = updates.get('aesthetic') or (normalized if initial else '')
    for style, aliases in STYLES.items():
        if any(term in style_text.casefold() for term in aliases):
            updates['style'] = style
            updates.setdefault('aesthetic', next(term for term in aliases if term in style_text.casefold()))
            break
    if not initial and not updates:
        return None
    known = set(values.get('clarified_fields', [])) | updates.keys()
    values.update(updates, clarified_fields=[field for field in QUESTIONS if field in known])
    return PlanNeeds.model_validate(values)


def next_clarification(needs, locale):
    index = 0 if locale == 'zh-CN' else 1
    return next((prompt[index] for field, prompt in QUESTIONS.items() if field not in needs.clarified_fields), None)
