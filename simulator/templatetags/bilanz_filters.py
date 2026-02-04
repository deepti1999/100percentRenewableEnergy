from django import template

register = template.Library()

@register.filter
def format_energy(value):
    """
    Format energy values for display in bilanz table.
    - Hides zeros (returns empty string)
    - Formats numbers with thousand separators and no decimals
    """
    try:
        num = float(value)
        if num == 0 or num == 0.0:
            return ""
        # Format with thousand separators (commas), no decimals
        return f"{int(round(num)):,}"
    except (ValueError, TypeError):
        return ""

@register.filter
def not_zero(value):
    """Check if value is not zero"""
    try:
        return float(value) != 0
    except (ValueError, TypeError):
        return False
