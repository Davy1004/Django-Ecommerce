from rest_framework.views import exception_handler


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
        first = data if isinstance(data, list) else next(iter(data.values()), "Invalid request")
        while isinstance(first, (list, tuple)) and first:
            first = first[0]
        if isinstance(data, dict) and isinstance(first, (str, bytes)):
            key = next(iter(data.keys()))
            message = str(first) if key == "non_field_errors" else f"{key}: {first}"
        else:
            message = str(first)
    response.data = {"error": message}
    if details is not None:
        response.data["details"] = details
    return response
