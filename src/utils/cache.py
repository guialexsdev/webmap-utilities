
from src.utils.webmapCommons import Utils


class Cache:
    def __init__(self, context):
        self.context = context

    def cachedSection(self, key, work):
        value = self.context.cachedValue(key)
        
        if value is None:            
            value = work()
            self.context.setCachedValue(key, value)
        
        return value