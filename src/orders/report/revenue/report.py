from datetime import datetime
from datetime import timedelta

import numpy as np
import pandas as pd
from django.db.models import Case
from django.db.models import CharField
from django.db.models import Count
from django.db.models import Sum
from django.db.models import Value
from django.db.models import When
from django.db.models.query import QuerySet

from core.settings import IMAGE_BASE_URL
from customers.models import Customer
from orders.models import Orders


def get_dashboard(queryset: QuerySet[Orders], date_from, date_to):
    date_from = datetime.strptime(date_from, "%Y-%m-%d").date() if date_from else (datetime.now() - timedelta(days=30)).date()
    date_to = datetime.strptime(date_to, "%Y-%m-%d").date() if date_to else datetime.now().date()
    # get order
    if queryset.exists():
        df_order = pd.DataFrame.from_records(
            queryset.values("price_total_order_actual", "complete_time", "transportation_care__status", "customer_id", "customer__created")
        ).sort_values(by=["complete_time"])
    else:
        return [], None

    total_customer = Customer.objects.filter(created__lte=date_from).count()

    df_order = df_order.assign(date=pd.to_datetime(df_order["complete_time"]).dt.date)

    df_order["old_customer"] = np.where(df_order["customer__created"].dt.date < date_from, 1, 0)
    df_order["new_customer"] = np.where(df_order["customer__created"].dt.date >= date_from, 1, 0)

    # calculate order completed
    df_order_completed = df_order[["date", "price_total_order_actual"]]

    df_total_order_completed = (
        df_order_completed.groupby("date")["price_total_order_actual"]
        .agg(["sum", "count"])
        .rename(
            columns={
                "sum": "total_price_actual",  # to rename total_price_order_completed
                "count": "total_order",  # to rename total_order_completed
            }
        )
        .reset_index()
    )
    df_order_old_new = df_order[["date", "customer_id", "old_customer", "new_customer"]]

    df_order_old_new.drop_duplicates(inplace=True)  # drop duplicate customer_id

    df_total_old_new_customer = (
        df_order_old_new.groupby("date")
        .agg(total_old_customer=("old_customer", "sum"), total_new_customer=("new_customer", "sum"))
        .reset_index()
    )

    df_total_order_completed = df_total_order_completed.merge(df_total_old_new_customer, on="date", how="left").fillna(0)

    df_total_order_completed["total_old_customer"] = df_total_order_completed["total_old_customer"].astype(int)
    df_total_order_completed["total_new_customer"] = df_total_order_completed["total_new_customer"].astype(int)

    df_total_order_completed["old_customer_return_rate"] = df_total_order_completed["total_old_customer"] / total_customer

    date_range = pd.date_range(start=date_from, end=date_to)

    # Chuyển đổi chuỗi ngày thành DataFrame
    df_date_range = pd.DataFrame(date_range, columns=["date"])
    df_date_range["date"] = df_date_range["date"].dt.date

    df_total_order_completed = df_date_range.merge(df_total_order_completed, on="date", how="left").fillna(0)

    df_total_order_completed = df_total_order_completed.astype(
        {"total_price_actual": "int", "total_order": "int", "total_old_customer": "int", "total_new_customer": "int"}
    )
    # purchase_rate
    df_total = df_total_order_completed[["total_price_actual", "total_order", "total_old_customer", "total_new_customer"]].sum()

    df_total["old_customer_return_rate"] = df_total["total_old_customer"] / total_customer

    total = df_total.replace([np.inf, -np.inf, np.nan], 0).to_dict()

    data = df_total_order_completed.replace([np.inf, -np.inf, np.nan], 0).to_dict(orient="records")
    return data, total


def get_revenue_by_product_variant(queryset: QuerySet[Orders]):
    if not queryset.exists():
        return [], None
    order_fields = [
        # order
        "order_key",
        "created",
        "status",
        "complete_time",
        "price_total_order_actual",
        # location
        "address_shipping__ward__district__province__label",
    ]
    item_fields = [
        # variants
        "line_items__id",
        "line_items__variant",
        "line_items__variant__SKU_code",
        "line_items__variant__name",  # => to group by
        "line_items__variant__type",
        "line_items__quantity",
        "line_items__price_total",
        "line_items__price_total_input",
        "line_items__variant__product__name",
        "line_items__variant__images__image",
        "line_items__variant__images__is_default",
        "line_items__variant__images__id",
    ]

    df_query = queryset.values(
        *order_fields,
        *item_fields,
    )
    df = pd.DataFrame.from_records(df_query)
    df = df.drop_duplicates(subset=["order_key", "line_items__id"])
    df['price_to_sum'] = df.apply(
        lambda row: row['line_items__price_total_input'] if pd.notnull(row['line_items__price_total_input']) or row['line_items__price_total_input'] > 0 else row['line_items__price_total'], axis=1
    )

    df_result = (
        df.groupby(["line_items__variant", "line_items__variant__SKU_code", "line_items__variant__name", "line_items__variant__type"])
        .agg(
            {
                "line_items__quantity": "sum",
                "price_to_sum": "sum",
                # "line_items__variant__images__image": lambda x: list(set(x)) if list(set(x)) != [None] else [],
                "line_items__variant__images__image": lambda x: list(set(x)),
                "line_items__variant__images__is_default": lambda x: list(set(x)),
                "line_items__variant__images__id": lambda x: list(set(x)),
            }
        )
        .reset_index()
        .sort_values(by=["line_items__quantity"], ascending=False)
    )

    df_result['images'] = df_result.apply(
        lambda row: [
            {"image": IMAGE_BASE_URL + img, "is_default": is_default, "id": img_id}
            for img, is_default, img_id in zip(row["line_items__variant__images__image"], row["line_items__variant__images__is_default"], row["line_items__variant__images__id"])
            if img is not None
        ],
        axis=1
    )

    df_result.drop(columns=["line_items__variant__images__image", "line_items__variant__images__is_default", "line_items__variant__images__id"], inplace=True)

    df_result.rename(
        columns={
            "line_items__variant": "variant_id",
            "line_items__variant__SKU_code": "SKU_code",
            "line_items__variant__name": "variant_name",
            "line_items__variant__type": "variant_type",
            "line_items__quantity": "total_quantity",
            "price_to_sum": "total_price",
        },
        inplace=True,
    )

    result = df_result.replace([np.inf, -np.inf, np.nan], 0).to_dict(orient="records")

    df_total = df_result[
        [
            "total_quantity",
            "total_price",
        ]
    ].sum()

    total = df_total.replace([np.inf, -np.inf, np.nan], 0).to_dict()

    return result, total


def get_revenue_by_sale(queryset: QuerySet[Orders]):
    if not queryset.exists():
        return [], None
    df = pd.DataFrame.from_records(
        queryset.values(
            "id",
            "customer__customer_care_staff",
            "customer__customer_care_staff__name",
            "value_cross_sale",
            "price_total_discount_order_promotion",
            "price_discount_input",
            "price_addition_input",
            "price_total_order_actual",
            "source__name",
        )
    )
    df = df.assign(total_discount=df["price_total_discount_order_promotion"] + df["price_discount_input"])
    df["is_crm"] = df["source__name"].str.contains("crm", case=False)
    df["revenue_crm"] = df["price_total_order_actual"].where(df["is_crm"], 0)
    
    df_commission = pd.DataFrame.from_records(
        queryset.values(
            "id",
            "customer__customer_care_staff",
            "line_items__commission_discount"
        )
    )

    df_commission_result = df_commission.groupby(["customer__customer_care_staff", "id"]).agg(
        {"line_items__commission_discount": "sum"}
    ).reset_index()

    df = df.merge(df_commission_result, on=["customer__customer_care_staff", "id"], how="left")
    
    df_result = df.groupby(["customer__customer_care_staff", "customer__customer_care_staff__name"]).agg(
        {
            "price_total_order_actual": ["sum", "count"],
            "value_cross_sale": "sum",
            "price_addition_input": "sum",
            "total_discount": "sum",
            "revenue_crm": "sum",
            "line_items__commission_discount": "sum",
        }
    ).reset_index()

    df_result.columns = ["_".join(x) if x[1] else x[0] for x in df_result.columns]  # Map column names to sum, count
    df_result.rename(
        columns={
            "customer__customer_care_staff": "sale_id",
            "customer__customer_care_staff__name": "sale_name",
            "price_total_order_actual_sum": "total_revenue",
            "price_total_order_actual_count": "total_order",
            "value_cross_sale_sum": "total_cross_sale",
            "price_addition_input_sum": "total_addition_price",
            "total_discount_sum": "total_discount",
            "revenue_crm_sum": "total_revenue_crm",
            "line_items__commission_discount_sum": "total_commission",
        },
        inplace=True,
    )
    
    df_result.sort_values(by=["total_order"], ascending=False, inplace=True)

    result = df_result.replace([np.inf, -np.inf, np.nan], 0).to_dict(orient="records")

    df_total = df_result[
        ["total_order", "total_revenue", "total_cross_sale", "total_addition_price", "total_discount", "total_revenue_crm", "total_commission"]
    ].sum()

    total = df_total.replace([np.inf, -np.inf, np.nan], 0).to_dict()

    return result, total


def get_revenue_by_source(queryset: QuerySet[Orders]):
    if not queryset.exists():
        return [], None
    df = pd.DataFrame.from_records(
        queryset.values(
            "id",
            "source",
            "source__name",
            "price_total_variant_all",
            "price_total_order_actual",
            "price_pre_paid",
            "payments",
            "payments__price_from_order",
            "payments__price_from_third_party",
            "payments__is_confirm",
        )
    )
    df.fillna({"payments__price_from_third_party": 0}, inplace=True)

    # lấy đơn hàng trả và chưa trả

    df["paid"] = np.where(df["payments__is_confirm"], df["payments__price_from_order"] + df["payments__price_from_third_party"], 0)
    df["unpaid"] = np.where(~df["payments__is_confirm"], df["payments__price_from_order"] + df["payments__price_from_third_party"], 0)
    df.drop(columns=["payments__price_from_order", "payments__price_from_third_party", "payments__is_confirm"], inplace=True)

    df_order = (
        df.groupby(["id", "source", "source__name", "price_total_variant_all", "price_total_order_actual", "price_pre_paid"])
        .agg({"paid": "sum", "unpaid": "sum"})
        .reset_index()
    )

    df_result = (
        df_order.groupby(["source", "source__name"])
        .agg(
            {
                "id": "count",
                "price_total_variant_all": "sum",
                "price_total_order_actual": "sum",
                "price_pre_paid": "sum",
                "paid": "sum",
                "unpaid": "sum",
            }
        )
        .reset_index()
    )

    df_result.rename(
        columns={
            "source": "source_id",
            "source__name": "source_name",
            "id": "total_order",
        },
        inplace=True,
    )

    result = df_result.replace([np.inf, -np.inf, np.nan], 0).to_dict(orient="records")

    df_total = df_result.agg(
        {
            "source_id": "nunique",
            "total_order": "sum",
            "price_total_variant_all": "sum",
            "price_total_order_actual": "sum",
            "price_pre_paid": "sum",
            "paid": "sum",
            "unpaid": "sum",
        }
    )

    total = df_total.replace([np.inf, -np.inf, np.nan], 0).to_dict()

    return result, total


def get_ratio_order_pre_and_current_month(queryset: QuerySet[Orders]):
    # Get today's date
    today = datetime.now()

    # Get the start and end dates for the current month
    start_date_current_month = datetime(today.year, today.month, 1)
    if today.month == 12:
        end_date_current_month = datetime(today.year + 1, 1, 1)
    else:
        end_date_current_month = datetime(today.year, today.month + 1, 1)

    # Get the start and end dates for the previous month
    start_date_pre_month = datetime(today.year, today.month - 1, 1) if today.month != 1 else datetime(today.year - 1, 12, 1)
    end_date_pre_month = start_date_current_month

    main_query = (
        queryset.filter(created__range=(start_date_pre_month, end_date_current_month))
        .annotate(
            order_month=Case(
                When(created__range=(start_date_current_month, end_date_current_month), then=Value("current_month")),
                When(created__range=(start_date_pre_month, end_date_pre_month), then=Value("pre_month")),
                default=Value("other"),
                output_field=CharField(),
            )
        )
        .values("order_month")
        .annotate(order_count=Count("id"), revenue_sum=Sum("price_total_order_actual"))
    )

    today_query = (
        queryset.filter(created__date=today.date())
        .values('created__date')
        .annotate(
            order_count=Count("id"),
            revenue_sum=Sum("price_total_order_actual"),
            order_month=Value('today', output_field=CharField())
        ).values('order_month', 'order_count', 'revenue_sum')
    )

    query = main_query.union(today_query)

    result = {
        "total_order_prev_month": 0,
        "total_price_actual_prev_month": 0,
        "total_order_current_month": 0,
        "total_price_actual_current_month": 0,
        "total_order_today": 0,
        "total_price_actual_today": 0,
    }
    for data in query:
        if data["order_month"] == "pre_month":
            result["total_order_prev_month"] = data["order_count"]
            result["total_price_actual_prev_month"] = data["revenue_sum"]
        elif data["order_month"] == "current_month":
            result["total_order_current_month"] = data["order_count"]
            result["total_price_actual_current_month"] = data["revenue_sum"]
        elif data["order_month"] == "today":
            result["total_order_today"] = data["order_count"]
            result["total_price_actual_today"] = data["revenue_sum"]

    return result
