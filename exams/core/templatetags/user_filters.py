from django import template

register = template.Library()


@register.filter
def addclass(field, css):
    return field.as_widget(attrs={'class': css})


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def timedelta(timedelta, cut):
    return str(timedelta)[:-cut]
