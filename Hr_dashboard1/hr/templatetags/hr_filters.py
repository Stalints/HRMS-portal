from django import template
import os

register = template.Library()

@register.filter
def basename(value):
    try:
        if not value:
            return ""
        name = value.name if hasattr(value, "name") else str(value)
        return os.path.basename(name)
    except Exception:
        return ""


@register.filter
def get_item(mapping, key):
    try:
        return mapping.get(key, "")
    except Exception:
        return ""
