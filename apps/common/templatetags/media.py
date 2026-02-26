from django import template

register = template.Library()


@register.simple_tag
def media_url(image_field):
    if not image_field:
        return ''
    try:
        return image_field.url
    except Exception:
        return ''
