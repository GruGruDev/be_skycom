import re

from rest_framework.validators import ValidationError


class PhoneValidator:
    regex = r"[0|+84|84]{0,4}[9|8|3|5|7]{1}[0-9]{6,10}"

    def __call__(self, phone):
        if not re.match(self.regex, phone):
            raise ValidationError(
                "Phone number must be a Vietnamese phone number, include 7-15 digits. \
                Example format: 098xxxxxxx, +8498xxxxxxx"
            )


def validate_min_max(value = None, min_value=None, max_value=None):
    if value and min_value is not None and value < min_value:
        raise ValidationError(f"Giá trị không được nhỏ hơn {min_value}.")
    if value and max_value is not None and value > max_value:
        raise ValidationError(f"Giá trị không được lớn hơn {max_value}.")