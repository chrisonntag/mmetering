from django import template

register = template.Library()

@register.filter(name="as_percentage_of")
def as_percentage_of(part, whole):
    if part > whole:
        result = (float(part) / whole * 100) - 100
    else:
        result = float(part) / whole * 100
    try:
        return "%d%%" % (result)
    except (ValueError, ZeroDivisionError):
        return ""