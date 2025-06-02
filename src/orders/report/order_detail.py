import datetime
import json
import math
from functools import reduce

import numpy as np
import pandas as pd
import pytz
from django.db.models import F
from django.db.models.query import QuerySet

from core.settings import TIME_ZONE
from orders.enums import OrderPaymentType
from orders.enums import WarehouseSheetType
from orders.models import Orders


def utc_to_local(dt: datetime.datetime):
    tz = pytz.timezone(TIME_ZONE)
    local_time = dt.astimezone(tz)
    return local_time


def calc_combo_price(df: pd.DataFrame):
    if not df["item_variant_total_neo"] or math.isnan(df["item_variant_total_neo"]):
        return 0
    if (df["discount_percent"] and not math.isnan(df["discount_percent"])) or (
        df["discount_amount"] and not math.isnan(df["discount_amount"])
    ):

        discount_amount = df["discount_amount"] if df["discount_amount"] else 0
        combo_total = df["item_variant_total_neo"]
        if df["discount_percent"] and not math.isnan(df["discount_percent"]):
            combo_actual_total = combo_total - (combo_total * df["discount_percent"] / 100)
            discount_amount = combo_total - combo_actual_total

        df["line_items__price_total"] = round(
            df["line_items__price_total_neo"] - (df["line_items__price_total_neo"] / combo_total * discount_amount),
            2,
        )
    return df["line_items__price_total"]


def list_order_item(queryset: QuerySet[Orders], *args, **kwargs):  # pylint: disable=R0915
    combo_to_item_fields_mapping = {
        "line_items__items_combo__id": "item_id",
        "line_items__items_combo__variant__SKU_code": "line_items__variant__SKU_code",
        "line_items__items_combo__variant__name": "line_items__variant__name",
        "line_items__items_combo__quantity": "line_items__quantity",
        "line_items__items_combo__variant__neo_price": "line_items__price_total_neo",
        # "line_items__items_combo__variant__neo_price": "line_items__price_total_neo",
        "line_items__price_total_neo": "item_variant_total_neo",  # need to check
        "line_items__quantity": "item_quantity",
        "line_items__items_combo__variant__product_variant_promotion_variant__percent_value": "discount_percent",
        "line_items__items_combo__variant__product_variant_promotion_variant__price_value": "discount_amount",
    }
    combo_exclude_fields = ["item_variant_total_neo", "item_quantity", "discount_percent", "discount_amount"]
    gift_to_item_fields_mapping = {
        "line_items__variant_promotions_used__id": "gift_id",
        "line_items__variant_promotions_used__promotion_variant__variant__SKU_code": "line_items__variant__SKU_code",
        "line_items__variant_promotions_used__promotion_variant__variant__name": "line_items__variant__name",
        "line_items__variant_promotions_used__items_promotion__quantity": "line_items__quantity",
        "line_items__variant_promotions_used__promotion_variant__name": "line_items__promotion__name",
        "line_items__variant_promotions_used__promotion_variant__variant__neo_price": "line_items__price_total_neo",
    }
    order_fields = [
        # order
        "order_key",
        "created",
        "created_by__name",
        "status",
        "complete_time",
        "modified_by__name",
        "is_print",
        "printed_at",
        "printed_by__name",
        "source__name",
        "price_delivery_input",
        "price_addition_input",
        "price_total_discount_order_promotion",
        "price_discount_input",
        # "promotion__name",
        "payments__note",
        "price_total_variant_all",
        "price_total_variant_actual",
        "price_total_order_actual",
        # "ecommerce_code",
        "sale_note",
        "phone_shipping",
        "name_shipping",
        # delivery
        "shipping__created",
        "shipping__tracking_number",
        "shipping__carrier_status",
        "shipping__modified",
        "shipping__note",
        "shipping__return_full_address",
        "shipping__return_name",
        "shipping__delivery_company_name",
        # location
        "address_shipping__address",
        "address_shipping__ward__label",
        "address_shipping__ward__district__label",
        "address_shipping__ward__district__province__label",
    ]
    item_fields = [
        # variants
        "line_items__id",
        "line_items__variant__SKU_code",
        "line_items__variant__name",
        "line_items__variant__type",
        "line_items__quantity",
        "line_items__variant_promotions_used__promotion_variant__name",
        "line_items__price_total_neo",
        "line_items__price_total",
    ]
    gifts = queryset.values(
        *order_fields,
        *item_fields,
        *combo_to_item_fields_mapping.keys(),
        *gift_to_item_fields_mapping.keys(),
    )
    item_gift_df = pd.DataFrame.from_records(gifts)
    if item_gift_df.empty:
        return []

    item_df = item_gift_df[[*order_fields, *item_fields]].drop_duplicates(subset=["line_items__id"])
    item_df["is_gift"] = item_df["line_items__price_total"].apply(lambda x: 1 if x == 0 else 0)
    gift_df = (
        item_gift_df[[*order_fields, *gift_to_item_fields_mapping.keys()]]
        .rename(columns=gift_to_item_fields_mapping)
        .dropna(subset=["gift_id"])
        .drop_duplicates(subset=["gift_id"])
    )
    gift_df["line_items__price_total"] = 0
    gift_df["is_gift"] = 1

    combo_df = (
        item_gift_df[[*order_fields, *combo_to_item_fields_mapping.keys()]]
        .rename(columns=combo_to_item_fields_mapping)
        .dropna(subset=["item_id"])
        .drop_duplicates(subset=["item_id"])
    )
    combo_df["line_items__price_total"] = combo_df["line_items__price_total_neo"]
    if not combo_df.empty:
        combo_df["line_items__price_total"] = combo_df.apply(calc_combo_price, axis=1)
    combo_df["is_gift"] = combo_df["line_items__price_total"].apply(lambda x: 1 if x == 0 else 0)
    combo_df.drop(["item_variant_total_neo"], axis=1)
    combo_df.dropna(subset=combo_exclude_fields)

    df = pd.concat([item_df, gift_df, combo_df]).sort_index()

    df["line_items__variant__type"] = df["line_items__variant__type"].apply(lambda x: "simple" if x != "combo" else None)
    df = df.dropna(subset=["line_items__variant__type"])
    df.drop(["line_items__variant__type"], axis=1)
    # df = gift_df

    df["created"] = df["created"].apply(lambda x: utc_to_local(x) if not pd.isna(x) else None)
    df["shipping__created"] = df["shipping__created"].apply(lambda x: utc_to_local(x) if not pd.isna(x) else None)
    df["complete_time"] = df["complete_time"].apply(lambda x: utc_to_local(x) if not pd.isna(x) else None)
    df["printed_at"] = df["printed_at"].apply(lambda x: utc_to_local(x) if not pd.isna(x) else None)
    df["shipping_address"] = reduce(
        lambda a, b: a.str.cat(b, sep=", "),
        [
            df["address_shipping__address"],
            df["address_shipping__ward__label"],
            df["address_shipping__ward__district__label"],
            df["address_shipping__ward__district__province__label"],
        ],
    )
    df.drop(
        columns=[
            "address_shipping__address",
            "address_shipping__ward__label",
            "address_shipping__ward__district__label",
            "address_shipping__ward__district__province__label",
        ],
        inplace=True,
    )

    payments = queryset.values("order_key", "payments__type", "payments__price_from_order", "payments__date_confirm")
    payments_df = pd.DataFrame.from_records(payments)
    payments_df["payment_cod"] = payments_df.loc[payments_df["payments__type"] == OrderPaymentType.COD, "payments__price_from_order"]
    payments_df["payment_cod_date"] = payments_df.loc[payments_df["payments__type"] == OrderPaymentType.COD, "payments__date_confirm"]
    payments_df["payment_cash"] = payments_df.loc[payments_df["payments__type"] == OrderPaymentType.CASH, "payments__price_from_order"]
    payments_df["payment_cash_date"] = payments_df.loc[payments_df["payments__type"] == OrderPaymentType.CASH, "payments__date_confirm"]
    payments_df["payment_direct_transfer"] = payments_df.loc[
        payments_df["payments__type"] == OrderPaymentType.DIRECT_TRANSFER, "payments__price_from_order"
    ]
    payments_df["payment_direct_transfer_date"] = payments_df.loc[
        payments_df["payments__type"] == OrderPaymentType.DIRECT_TRANSFER, "payments__date_confirm"
    ]

    payments_order = (
        payments_df.groupby("order_key", as_index=False)[["payment_cod", "payment_cash", "payment_direct_transfer"]].sum().fillna(0)
    )
    payments_order_date = payments_df.groupby("order_key", as_index=False)[
        ["payment_cod_date", "payment_cash_date", "payment_direct_transfer_date"]
    ].max()

    sheets = queryset.annotate(
        sheets_code=F("warehouse_sheet_import_export_order__code"),
        sheets_type=F("warehouse_sheet_import_export_order__type"),
        sheets_is_confirm=F("warehouse_sheet_import_export_order__is_confirm"),
        sheets_confirm_date=F("warehouse_sheet_import_export_order__confirm_date"),
    ).values(
        "order_key",
        "sheets_code",
        "sheets_type",
        "sheets_is_confirm",
        "sheets_confirm_date",
    )
    sheets_df = pd.DataFrame.from_records(sheets)
    sheets_df["imported"] = (sheets_df["sheets_type"] == WarehouseSheetType.Import) & (sheets_df["sheets_is_confirm"])
    sheets_df["exported"] = (sheets_df["sheets_type"] == WarehouseSheetType.Export) & (sheets_df["sheets_is_confirm"])
    sheets_df["imported_date"] = sheets_df.loc[sheets_df["sheets_type"] == WarehouseSheetType.Import, "sheets_confirm_date"]
    sheets_df["exported_date"] = sheets_df.loc[sheets_df["sheets_type"] == WarehouseSheetType.Export, "sheets_confirm_date"]
    sheets_order = sheets_df.groupby("order_key", as_index=False)[["imported", "exported", "imported_date", "exported_date"]].max()

    tags = queryset.values(
        "order_key",
        "tags__name",
    )
    tags_df = pd.DataFrame.from_records(tags)
    tags_df["tags__name"] = tags_df["tags__name"].apply(lambda x: x if x else "")
    tags_order = tags_df.groupby("order_key", as_index=False)[["tags__name"]].agg(", ".join)

    promotions = queryset.annotate(promotions_name=F("promotions_used__promotion_order__name")).values("order_key", "promotions_name")
    promotions_df = pd.DataFrame.from_records(promotions)
    promotions_df["promotions_name"] = promotions_df["promotions_name"].apply(lambda x: x if x else "")
    promotions_order = promotions_df.groupby("order_key", as_index=False)[["promotions_name"]].agg(", ".join)

    result = (
        df.merge(sheets_order, on="order_key", how="left")
        .merge(payments_order, on="order_key", how="left")
        .merge(payments_order_date, on="order_key", how="left")
        .merge(tags_order, on="order_key", how="left")
        .merge(promotions_order, on="order_key", how="left")
    )

    # convert uuid to str
    columns = ["line_items__id", "gift_id", "item_id"]
    result[columns] = result[columns].astype(str).replace("nan", np.nan)

    result = json.loads(result.to_json(orient="records", date_format="iso"))

    return result


def list_order(queryset: QuerySet[Orders], *args, **kwargs):
    orders = queryset.values(
        # order
        "order_key",
        "created",
        "created_by__name",
        "status",
        "complete_time",
        "modified_by__name",
        "is_print",
        "printed_at",
        "printed_by__name",
        "source__name",
        "price_delivery_input",
        "price_addition_input",
        "price_total_discount_order_promotion",
        "price_discount_input",
        "payments__note",
        "price_total_variant_all",
        "price_total_variant_actual",
        "price_total_order_actual",
        "price_total_variant_actual_input",
        "sale_note",
        "phone_shipping",
        "name_shipping",
        # delivery
        "shipping__created",
        "shipping__tracking_number",
        "shipping__carrier_status",
        "shipping__modified",
        "shipping__note",
        "shipping__return_full_address",
        "shipping__return_name",
        "shipping__delivery_company_name",
        "address_shipping__address",
        "address_shipping__ward__label",
        "address_shipping__ward__district__label",
        "address_shipping__ward__district__province__label",
        # tags_list=ArrayAgg('tags__name', default=Value([]))
    )
    df = pd.DataFrame.from_records(orders)
    df["created"] = df["created"].apply(lambda x: utc_to_local(x) if not pd.isna(x) else None)
    df["shipping__created"] = df["shipping__created"].apply(lambda x: utc_to_local(x) if not pd.isna(x) else None)
    df["complete_time"] = df["complete_time"].apply(lambda x: utc_to_local(x) if not pd.isna(x) else None)
    df["printed_at"] = df["printed_at"].apply(lambda x: utc_to_local(x) if not pd.isna(x) else None)
    # Get full address
    df["shipping_address"] = reduce(
        lambda a, b: a.str.cat(b, sep=", "),
        [
            df["address_shipping__address"],
            df["address_shipping__ward__label"],
            df["address_shipping__ward__district__label"],
            df["address_shipping__ward__district__province__label"],
        ],
    )
    df.drop(
        columns=[
            "address_shipping__address",
            "address_shipping__ward__label",
            "address_shipping__ward__district__label",
            "address_shipping__ward__district__province__label",
        ],
        inplace=True,
    )

    payments = queryset.values("order_key", "payments__type", "payments__price_from_order", "payments__date_confirm")
    payments_df = pd.DataFrame.from_records(payments)
    payments_df["payment_cod"] = payments_df.loc[payments_df["payments__type"] == OrderPaymentType.COD, "payments__price_from_order"]
    payments_df["payment_cod_date"] = payments_df.loc[payments_df["payments__type"] == OrderPaymentType.COD, "payments__date_confirm"]
    payments_df["payment_cash"] = payments_df.loc[payments_df["payments__type"] == OrderPaymentType.CASH, "payments__price_from_order"]
    payments_df["payment_cash_date"] = payments_df.loc[payments_df["payments__type"] == OrderPaymentType.CASH, "payments__date_confirm"]
    payments_df["payment_direct_transfer"] = payments_df.loc[
        payments_df["payments__type"] == OrderPaymentType.DIRECT_TRANSFER, "payments__price_from_order"
    ]
    payments_df["payment_direct_transfer_date"] = payments_df.loc[
        payments_df["payments__type"] == OrderPaymentType.DIRECT_TRANSFER, "payments__date_confirm"
    ]
    payments_order = (
        payments_df.groupby("order_key", as_index=False)[["payment_cod", "payment_cash", "payment_direct_transfer"]].sum().fillna(0)
    )
    payments_order_date = payments_df.groupby("order_key", as_index=False)[
        ["payment_cod_date", "payment_cash_date", "payment_direct_transfer_date"]
    ].max()

    sheets = queryset.annotate(
        sheets_code=F("warehouse_sheet_import_export_order__code"),
        sheets_type=F("warehouse_sheet_import_export_order__type"),
        sheets_is_confirm=F("warehouse_sheet_import_export_order__is_confirm"),
        sheets_confirm_date=F("warehouse_sheet_import_export_order__confirm_date"),
    ).values(
        "order_key",
        "sheets_code",
        "sheets_type",
        "sheets_is_confirm",
        "sheets_confirm_date",
    )
    sheets_df = pd.DataFrame.from_records(sheets)
    sheets_df["imported"] = (sheets_df["sheets_type"] == WarehouseSheetType.Import) & (sheets_df["sheets_is_confirm"])
    sheets_df["exported"] = (sheets_df["sheets_type"] == WarehouseSheetType.Export) & (sheets_df["sheets_is_confirm"])
    sheets_df["imported_date"] = sheets_df.loc[sheets_df["sheets_type"] == WarehouseSheetType.Import, "sheets_confirm_date"]
    sheets_df["exported_date"] = sheets_df.loc[sheets_df["sheets_type"] == WarehouseSheetType.Export, "sheets_confirm_date"]
    sheets_order = sheets_df.groupby("order_key", as_index=False)[["imported", "exported", "imported_date", "exported_date"]].max()

    tags = queryset.values(
        "order_key",
        "tags__name",
    )
    tags_df = pd.DataFrame.from_records(tags)
    tags_df["tags__name"] = tags_df["tags__name"].apply(lambda x: x if x else "")
    tags_order = tags_df.groupby("order_key", as_index=False)[["tags__name"]].agg(", ".join)

    promotions = queryset.annotate(promotions_name=F("promotions_used__promotion_order__name")).values("order_key", "promotions_name")
    promotions_df = pd.DataFrame.from_records(promotions)
    promotions_df["promotions_name"] = promotions_df["promotions_name"].apply(lambda x: x if x else "")
    promotions_order = promotions_df.groupby("order_key", as_index=False)[["promotions_name"]].agg(", ".join)

    result = (
        df.merge(sheets_order, on="order_key", how="left")
        .merge(payments_order, on="order_key", how="left")
        .merge(payments_order_date, on="order_key", how="left")
        .merge(tags_order, on="order_key", how="left")
        .merge(promotions_order, on="order_key", how="left")
    )

    result = json.loads(result.to_json(orient="records", date_format="iso"))
    return result
