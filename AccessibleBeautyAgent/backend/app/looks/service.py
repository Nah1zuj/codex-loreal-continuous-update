class LookService:
    def __init__(self, store,settings=None):
        self.store = store
        self.settings=settings
    def search(self, scene, desired_impression, avoid, preferences=None):
        def score(look):
            return 5*(scene in look['scene']) + 2*len(set(desired_impression)&set(look['desired_impression'])) + len(set(avoid)&set(look['avoid'])) + (1 if (preferences or {}).get('preferred_saturation') == look['lip']['saturation'] else 0)
        from app.knowledge.policy import eligible
        usable=[look for look in self.store.looks if eligible(look,self.settings) and look.get('routine_id') in self.store.routine_map and eligible(self.store.routine_map[look['routine_id']],self.settings)]
        ranked = sorted(usable,key=score,reverse=True)
        return [{'look':x,'score':score(x)} for x in ranked]
