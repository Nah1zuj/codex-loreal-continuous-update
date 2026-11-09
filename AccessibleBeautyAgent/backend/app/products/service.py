from app.knowledge.policy import eligible


def describe_product(product):
    label = product.get('name') or product.get('category') or '产品信息不可用'
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
        rows = sorted([p for p in self.store.products if eligible(p,self.settings)],key=score,reverse=True)
        return [{**p,'score':score(p),'description':describe_product(p)} for p in rows if look_id in p['look_ids']][:6]
    def available_products(self):
        return {p['product_id']:p for p in self.store.products if eligible(p,self.settings)}

    def sources(self, product):
        source_map = {row['source_id']: row for row in self.store.sources}
        return [
            {key: source_map[source_id].get(key) for key in ('source_id','title','url','accessed_at')}
            for source_id in product.get('source_ids',[])
            if source_id in source_map and source_map[source_id].get('url')
            and source_map[source_id].get('status') not in ('REJECTED','DEPRECATED')
        ]

    def catalog(self):
        return [
            {key: product[key] for key in ('product_id','name','category')}
            for product in self.available_products().values()
        ]

    def compare(self, ids):
        products = self.available_products()
        results = []
        for product_id in ids:
            product = products.get(product_id)
            if not product:
                results.append({'product_id':product_id,'description':'产品信息不可用','evidence_kind':'unavailable',
                                'attributes':{},'sources':[],'review_status':None})
                continue
            sources = self.sources(product)
            demo = bool(product.get('demo_data') or product.get('source_type') == 'sample')
            evidence_kind = 'demo' if demo else 'source' if sources else 'unavailable'
            attributes = {field:product.get(field) or None for field in
                          ('name','category','finish','saturation','undertone')} if demo or sources else {}
            results.append({
                'product_id':product_id,'description':describe_product(product) if demo or sources else '缺少可追溯的产品资料',
                'evidence_kind':evidence_kind,'attributes':attributes,'sources':[] if demo else sources,
                'review_status':product.get('status'),
            })
        return results
