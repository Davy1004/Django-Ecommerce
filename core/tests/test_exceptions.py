from core.exceptions import _first_message


def test_nested_error_is_flattened_to_one_readable_line():
    data = {"items": [{"quantity": ["Ensure this value is less than or equal to 100."]}]}
    assert _first_message(data) == "items.0.quantity: Ensure this value is less than or equal to 100."


def test_plain_field_error():
    assert _first_message({"phone": ["Enter a valid phone number."]}) == "phone: Enter a valid phone number."
