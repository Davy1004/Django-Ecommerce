from rest_framework.views import exception_handler


def _first_message(data, path=""):
    """Walk nested serializer errors to the first leaf: 'items.0.quantity' -> a readable line."""
    if isinstance(data, dict):
        for key, value in data.items():
            found = _first_message(value, path if key == "non_field_errors" else (f"{path}.{key}" if path else key))
            if found:
                return found
        return "Invalid request"
    if isinstance(data, (list, tuple)):
        for i, value in enumerate(data):
            found = _first_message(value, path if not isinstance(value, (dict, list, tuple)) else (f"{path}.{i}" if path else str(i)))
            if found:
                return found
        return ""
    text = str(data)
    return f"{path}: {text}" if path else text


def api_exception_handler(exc, context):
    """Every error looks like {"error": "<one readable message>", "details": ...}.

    The Next.js client only needs to read `error`; `details` keeps the per-field
    information for forms.
    """
    response = exception_handler(exc, context)
    if response is None or not isinstance(response.data, (dict, list)):
        return response
    data = response.data
    if isinstance(data, dict) and "error" in data:
        return response
    if isinstance(data, dict) and "detail" in data:
        message, details = str(data["detail"]), None
    else:
        details = data
        message = _first_message(data)
    response.data = {"error": message}
    if details is not None:
        response.data["details"] = details
    return response
