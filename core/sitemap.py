from django.contrib.sitemaps import Sitemap
from .models import Product


class ProductSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.9

    def items(self):
        return Product.objects.active()
    
    def lastmod(self,obj):
        return obj.updated
