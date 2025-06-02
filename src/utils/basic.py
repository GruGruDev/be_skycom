import re
from urllib.parse import parse_qs
from urllib.parse import urlsplit

import numpy as np
from rest_framework.exceptions import ValidationError

PHONE_REGEX = r"(?<!\d)(0|84|\+84)([1-9][0-9])([0-9]{7})(?!\d)"


def parse_utm_url(url, dimension, null_value="Chưa có"):
    params_dict = parse_qs(urlsplit(url).query)
    utm_source = params_dict["utm_source"][0].split("-") if params_dict.get("utm_source", None) else []
    utm_medium = params_dict["utm_medium"][0].split("-") if params_dict.get("utm_medium", None) else []
    utm_campaign = params_dict["utm_campaign"][0].split("-") if params_dict.get("utm_campaign", None) else []
    result = {
        "ad_channel": utm_source[0] if utm_source else null_value,
        "ad_account": utm_medium[0] if utm_medium else null_value,
        "ad_partner": utm_campaign[0] if utm_campaign else null_value,
        "ad_product_code": utm_campaign[1] if len(utm_campaign) >= 2 else null_value,
    }
    if dimension in result:
        return result[dimension]
    ad_id_content, ad_campaign_type = (utm_medium[1], utm_medium[2]) if len(utm_medium) >= 3 else (null_value, null_value)
    if len(utm_medium) == 2:
        ad_id_content, ad_campaign_type = (
            (null_value, utm_medium[1]) if re.search(r"[a-zA-Z]", utm_medium[1]) else (utm_medium[1], null_value)
        )
    result = {"ad_id_content": ad_id_content.split(".")[0], "ad_campaign_type": ad_campaign_type}
    return result[dimension]


def parse_ad_id(url):
    params_dict = parse_qs(urlsplit(url).query)
    ad_id_keyword = next(iter([x for x in params_dict if "ad_id" in x]), None)
    ad_id = next(iter(params_dict.get(ad_id_keyword, [])), None)
    adset_id = next(iter(params_dict.get("adset_id", [])), None)
    adgroup_id = next(iter(params_dict.get("adgroup_id", [])), None)
    campaign_id = next(iter(params_dict.get("campaign_id", [])), None)

    return {
        "ad_id": ad_id,
        "adset_id": adset_id,
        "adgroup_id": adgroup_id,
        "campaign_id": campaign_id,
    }


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[-1].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def convert_phone(phone: str) -> str:
    if len(phone) == 9 and phone[0] != 0:
        phone = "0" + phone
    return phone


def validate_phone(phone: str) -> bool:
    if not phone or phone is np.nan:
        return False
    phone_regex = PHONE_REGEX
    pattern = re.compile(phone_regex)
    phone_match = re.fullmatch(pattern, phone)
    # Kiểm tra match với chuỗi phone
    if phone_match:
        return True
    return False

def data_multi_sortby(data_result: list[dict], sortby: list[str]):
    if not sortby or len(data_result) == 0:
        return data_result
    
    sort_keys = [(key[1:], True) if key.startswith('-') else (key, False) for key in sortby]

    for sort_key, _ in sort_keys:
        if sort_key not in data_result[0]:
            raise ValidationError(f"{sort_key} is an invalid key")
    
    # Separate data with null values for sorting later
    null_data = []
    data = []
    for item in data_result:
        if any(item[key] is None for key, _ in sort_keys):
            null_data.append(item)
        else:
            data.append(item)

    # Sort data based on multiple keys
    for sort_key, des in reversed(sort_keys):
        data = sorted(data, key=lambda x: x[sort_key], reverse=des)
    
    result = data + null_data if sort_keys[-1][1] else null_data + data
    
    return result


def data_sortby(data_result: list[dict], sortby: str):
    if sortby is None or len(data_result) == 0:
        return data_result
    if len(sortby.split(",")) > 1:
        return data_multi_sortby(data_result, sortby.split(","))
    sort_key, des = (sortby, False) if sortby[0] != "-" else (sortby[1:], True)
    if sort_key not in data_result[0]:
        raise ValidationError(f"{sort_key} is invalid key")
    null_data = [x for x in data_result if x[sort_key] is None]
    data = [x for x in data_result if x[sort_key] is not None]
    sorted_data = sorted(data, key=lambda x: x[sort_key], reverse=des)
    result = sorted_data + null_data if des else null_data + sorted_data
    return result
