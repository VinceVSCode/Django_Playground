from django import template

register =  template.Library()

@register.simple_tag(takes_context=True)
def qs_keep (context, **overrides):
    """
    Build a querystring preserving current GET params, with optional overrides.

    Usage:
      {% qs_keep page=num %}      -> returns "page=2&tag=5&q=hello" (preserves other GET keys)
      {% qs_keep page=1 tag=None %} -> removes tag, sets page=1

    Note: Values of None remove that key.
    """
    request =  context.get('requests')
    if not request:
        return ''
    
    #start from current GET params
    params =  request.GET.copy()

    #apply overrides
    for key, val in overrides.items():
        if val is None:
            params.pop(key, None)  #remove this key
        else:
            params[key] = val    #set/override this key

    #return encoded qs without leading '?'
    return params.urlencode()