import django_filters
from core.models import Product, Task

class ProductFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(field_name="name",lookup_expr="icontains")
    class Meta:
        model = Product
        fields  = {
            "price":['lt','gt','exact'],
            "created":['year','month','year__gt','year__lt'],
            "name":['iexact','istartswith','icontains']
        }
    

class TaskFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr = 'icontains' )
    assigned = django_filters.CharFilter(field="assigned",lookup_expr = "username__iexact")
    class Meta:
        model = Task
        fields = ['status']


session_filter_pack = {
    'page_size':12,
    'sort_by':'latest',
}