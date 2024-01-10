from django import template
from core.models import Task, Product
from django.utils.safestring import mark_safe
import markdown

register = template.Library()

@register.simple_tag
def total_task():
    return Task.submitted.count()

@register.simple_tag(name = "total_product_count")
def product_count():
    return Product.objects.count()

@register.filter(name="lower")
def lowercase(value):
    return value.lower()

@register.filter(name="markdown")
def markdown_format(text):
    return mark_safe(markdown.markdown(text))

@register.filter(name="integer")
def integer_format(number):
    return int(number)

@register.inclusion_tag("post_inclusion_template.html")
def most_viewed_post():
    pass