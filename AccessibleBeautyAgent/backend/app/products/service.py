def describe_product(product):
    label = f"{product.get('brand','品牌信息不可用')}，{product.get('category','类别信息不可用')}"
    fields = [('finish','妆效'),('saturation','饱和度'),('undertone','底调')]
    descriptions = [f"{title}：{product.get(field) or '信息不可用'}" for field,title in fields]
    claims = product.get('claims') or []
    descriptions.append('声明：' + ('；'.join(claims) if claims else '信息不可用'))
    if product.get('source_type') == 'sample':
        descriptions.insert(0,'虚构演示产品，不是购买建议')
    return label + '。' + '。'.join(descriptions)

class ProductService:
    def __init__(self, store, settings):
        self.store, self.weights = store, settings.product_weights
        self.settings=settings
    def search(self, look_id, scene, preferences=None):
        preferences = preferences or {}
        def score(p):
            w = self.weights
            return w['scene']*(scene in p['contexts']) + w['look']*(look_id in p['look_ids']) + w['finish']*(p.get('finish') in preferences.get('preferred_finish',[])) + w['preference']*(p.get('saturation') == preferences.get('preferred_saturation')) - w['risk']*(p.get('finish') in preferences.get('avoid',[]))
        from app.knowledge.policy import eligible
        rows = sorted([p for p in self.store.products if eligible(p,self.settings)],key=score,reverse=True)
        return [{**p,'score':score(p),'description':describe_product(p)} for p in rows if look_id in p['look_ids']][:6]
    def compare(self, ids):
        from app.knowledge.policy import eligible
        products = {p['product_id']:p for p in self.store.products if eligible(p,self.settings)}
        return [{'product_id':pid,'description':describe_product(products[pid]) if pid in products else '产品信息不可用'} for pid in ids]
