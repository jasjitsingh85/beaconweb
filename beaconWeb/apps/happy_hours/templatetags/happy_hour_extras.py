from django import template

register = template.Library()

@register.filter(name='clean_string')
def clean_string(value):
    return value.replace("'","").replace("&","").replace("!","").replace("/","").replace("-","").replace(".","")