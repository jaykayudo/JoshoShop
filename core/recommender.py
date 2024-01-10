from django.conf import settings
import redis
from .models import Product

import uuid

#connect to Redis
r = redis.Redis(
    settings.REDIS_HOST,
    settings.REDIS_PORT,
    settings.REDIS_DB
)

class Recommender:
    def get_product_key(self,id):
        return f"product:{id}:purchased_with"
    
    def products_bought(self,products):
        product_ids = [p.id.urn for p in products]
        for product_id in product_ids:
            for with_id in product_ids:
                if product_id != with_id:
                    r.zincrby(
                        self.get_product_key(str(product_id)),
                        1,
                        str(with_id)
                    )
    def suggest_products_for(self,products,max_results = 6):
        def map_function(x):
            string_val = x[9:].decode()
            return uuid.UUID(string_val)
        product_ids = [p.id.urn for p in products]
        if len(product_ids) == 1:
            suggestions = r.zrange(self.get_product_key(str(product_ids[0])),0,-1,desc=True)[:max_results]
        else:
            # generate temporary key
            flat_ids = ''.join([str(id) for id in product_ids])
            temp_key = f"tmp_{flat_ids}"
            keys = [self.get_product_key(str(id)) for id in product_ids]
            r.zunionstore(temp_key,keys)

            r.zrem(temp_key,*product_ids)

            suggestions = r.zrange(temp_key,0,-1,desc=True)[:max_results]
            r.delete(temp_key)
        
        suggested_product_ids = [id for id in suggestions]

        # Create UUID from the string
        # print(suggested_product_ids)
        suggested_product_ids = list(map(map_function, suggested_product_ids))

        

        suggested_products = list(Product.objects.filter(id__in = suggested_product_ids))
        suggested_products.sort(key = lambda x: suggested_product_ids.index(x.id))
        return suggested_products
    
    def clear_purchases(self):
        product_ids = Product.objects.all().values_list("id", flat=True)
        for id in product_ids:
            r.delete(self.get_product_key(id))
