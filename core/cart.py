from decimal import Decimal
from .models import Product
from django.conf import settings

class Cart:
    def __init__(self,request):
        self.session = request.session
        if settings.CART_SESSION_ID in self.session:
            self.cart = self.session[settings.CART_SESSION_ID]
        else:
            self.cart = self.session[settings.CART_SESSION_ID] = {}
        self.save()
    
    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())
    def __iter__(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in = product_ids)
        cart = self.cart.copy()
        for product in products:
            item = cart[str(product.id)]
            product.quantity = item['quantity']
            product.total_price = str(Decimal(item['price']) * item['quantity'])
            yield product
        # for item in cart.values():
        #     item['price'] = str(item['price'])
        #     item['total_price'] = str(Decimal(item['price']) * item['quantity'])
        #     yield item

    def add(self, product, quantity = 1, override_quantity = False):
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {
                "quantity": 0,
                "price": str(product.price)
            }
        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += 1
        self.save()

    def remove(self,product):
        product_id = str(product.id)

        if product_id in self.cart:
            del self.cart[product_id]
            self.save()
    def change_quantity(self,product,quantity):
        product_id =  str(product.id)
        if product_id not in self.cart:
            return
       
        if quantity > 0:
            self.cart[product_id]['quantity'] = quantity
            self.save()
                
    
    def clear(self):
        if settings.CART_SESSION_ID in self.session:
            del self.session[settings.CART_SESSION_ID]
            self.save()
    def get_total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())


    def save(self):
        self.session.modified = True