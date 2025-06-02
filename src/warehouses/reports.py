from datetime import datetime
from datetime import timedelta

from collections import defaultdict
import uuid

from django.db.models import Case
from django.db.models import F
from django.db.models import Q
from django.db.models import IntegerField
from django.db.models import Max
from django.db.models import Min
from django.db.models import Sum
from django.db.models import Value
from django.db.models import When
from django.db.models.expressions import Window
from django.db.models.functions import RowNumber
from django.db.models.functions import TruncDate
import pandas as pd
from core.settings import IMAGE_BASE_URL
from files.models import Images
from products.models import ProductCategory
from warehouses.models import WarehouseInventory
from warehouses.models import WarehouseInventoryLog


class ReportWarehouse:
    """Báo số lượng `tồn kho`, `xuất kho`, `nhập kho` tại 1 khoảng thời gian"""

    def __init__(self, warehouse_ids: list, date_from: datetime, date_to: datetime, search: str) -> (None):
        self.warehouse_ids = warehouse_ids
        self.date_from = date_from
        date_end = date_to if date_to else datetime.now().date()
        self.date_to = date_end + timedelta(days=1)
        self.search = search

    def caculate_inventory_to_date_warehouse(self, datetime_filter, exp: str) -> (dict):
        """Danh sách và số lượng tồn của các lô trong kho hàng tại thời gian chỉ định"""
        latest_historical_inventories = WarehouseInventory.history.model.objects.select_related("product_variant_batch").prefetch_related(
            "product_variant_batch__product_variant",
            "product_variant_batch__product_variant__product",
            "product_variant_batch__product_variant__product__category",
        )
        if self.warehouse_ids:
            latest_historical_inventories = latest_historical_inventories.filter(warehouse_id__in=self.warehouse_ids)
        if datetime_filter:
            if exp == "<=":
                latest_historical_inventories = latest_historical_inventories.filter(history_date__lte=datetime_filter)
            elif exp == "<":
                latest_historical_inventories = latest_historical_inventories.filter(history_date__lt=datetime_filter)
            latest_historical_inventories = latest_historical_inventories.annotate(
                row_number=Window(
                    expression=RowNumber(),
                    partition_by=[F("product_variant_batch_id"), F("warehouse_id")],
                    order_by=F("history_date").desc(),
                )
            ).filter(row_number=1)
        else:
            latest_historical_inventories = latest_historical_inventories.annotate(
                row_number=Window(
                    expression=RowNumber(),
                    partition_by=[F("product_variant_batch_id"), F("warehouse_id")],
                    order_by=F("history_date").asc(),
                )
            ).filter(row_number=1)

        # Step 1: Filter HistoricalInventory

        latest_historical_inventories = latest_historical_inventories.annotate(
            product_variant_id=F("product_variant_batch__product_variant_id"),
            product_variant_name=F("product_variant_batch__product_variant__name"),
            product_variant_SKU=F("product_variant_batch__product_variant__SKU_code"),
            product_variant_price=F("product_variant_batch__product_variant__sale_price"),
            product_id=F("product_variant_batch__product_variant__product_id"),
            product_name=F("product_variant_batch__product_variant__product__name"),
            product_SKU_code=F("product_variant_batch__product_variant__product__SKU_code"),
            category_id=F("product_variant_batch__product_variant__product__category_id"),
            category_name=F("product_variant_batch__product_variant__product__category__name"),
        ).filter(product_variant_batch__product_variant_id__isnull=False)

        if self.search:
            search_query = Q(product_name__icontains=self.search) | \
                        Q(product_SKU_code__icontains=self.search) | \
                        Q(product_variant_SKU__icontains=self.search) | \
                        Q(product_variant_name__icontains=self.search) | \
                        Q(product_variant_batch__name__icontains=self.search)
            latest_historical_inventories = latest_historical_inventories.filter(search_query)
        
        latest_historical_inventories = latest_historical_inventories.values(
            "product_variant_batch_id",
            "quantity",
            "product_variant_id",
            "product_variant_name",
            "product_variant_SKU",
            "product_variant_price",
            "product_id",
            "product_name",
            "product_SKU_code",
            "history_date",
            "category_id",
            "category_name",
            "warehouse_id",
            "history_type",
        ).all()

        dataset = {}

        for inventory in latest_historical_inventories:
            key = str(inventory["product_variant_batch_id"]) + ":" + str(inventory["warehouse_id"])
            record = dataset[key] if dataset.get(key) else None
            if not record:
                dataset[key] = {
                    "quantity": inventory["quantity"],
                    "product_id": inventory["product_id"],
                    "product_name": inventory["product_name"],
                    "product_SKU_code": inventory["product_SKU_code"],
                    "variant_id": inventory["product_variant_id"],
                    "variant_name": inventory["product_variant_name"],
                    "variant_SKU": inventory["product_variant_SKU"],
                    "variant_price": inventory["product_variant_price"],
                    "category_id": inventory["category_id"],
                    "category_name": inventory["category_name"],
                    "history_date": inventory["history_date"],
                    "history_type": inventory["history_type"],
                }
            else:
                dataset[key].update(
                    {
                        "quantity": record.get("quantity", 0) + inventory["quantity"],
                    }
                )
        return dataset

    def caculate_import_export_warehouse(self) -> (dict):
        "Số lượng `xuất kho`, `nhập kho` theo từng lô trong kho hàng tại 1 khoảng thời gian"
        inventory_log = WarehouseInventoryLog.objects.select_related("product_variant_batch", "warehouse").all()
        if self.warehouse_ids:
            inventory_log = inventory_log.filter(warehouse_id__in=self.warehouse_ids)

        c_export_query = Q(quantity__lt=0)
        c_import_query = Q(quantity__gt=0)
        if self.date_from:
            c_export_query.add(Q(modified__gte=self.date_from), Q.AND)
            c_import_query.add(Q(modified__gte=self.date_from), Q.AND)
        if self.date_to:
            c_export_query.add(Q(modified__lt=self.date_to), Q.AND)
            c_import_query.add(Q(modified__lt=self.date_to), Q.AND)

        inventory_log = (
            inventory_log.values("warehouse_id", "product_variant_batch_id", "warehouse__name", "product_variant_batch__name")
            .annotate(
                c_export=Sum(Case(When(Q(c_export_query), then="quantity"), output_field=IntegerField(), default=Value(0))),
                c_import=Sum(Case(When(Q(c_import_query), then="quantity"), output_field=IntegerField(), default=Value(0))),
                latest_modified=Max("modified"),
                earliest_modified=Min("modified"),
            )
            .order_by("warehouse_id")
            .all()
        )

        result = {}
        for inv in inventory_log:
            batch_id = inv["product_variant_batch_id"]
            warehouse_data = {
                "warehouse_id": inv["warehouse_id"],
                "warehouse_name": inv["warehouse__name"],
                "c_export": inv.get("c_export"),
                "c_import": inv.get("c_import"),
                "batch_name": inv.get("product_variant_batch__name"),
                "expire_date": inv.get("product_variant_batch__expire_date"),
                "latest_modified": inv.get("latest_modified"),
                "earliest_modified": inv.get("earliest_modified"),
            }

            if batch_id in result:
                result[batch_id].append(warehouse_data)
            else:
                result[batch_id] = [warehouse_data]
        return result

    def get_data_process_report(self) -> dict:
        inventory_first: dict = self.caculate_inventory_to_date_warehouse(datetime_filter=self.date_from, exp="<=")
        count_import_export: dict = self.caculate_import_export_warehouse()
        inventory_last: dict = self.caculate_inventory_to_date_warehouse(datetime_filter=self.date_to, exp="<")

        report_dict = {}
        variant_batches = defaultdict(list)
        for k, v in inventory_last.items():
            product_id = str(v.get("product_id"))
            product_name = str(v.get("product_name"))
            product_SKU_code = str(v.get("product_SKU_code"))
            variant_id = str(v.get("variant_id"))
            variant_name = str(v.get("variant_name"))
            variant_SKU_code = str(v.get("variant_SKU"))
            variant_price = str(v.get("variant_price"))
            category_id = str(v.get("category_id"))
            category_name = str(v.get("category_name"))

            if report_dict.get(product_id) is None:
                report_dict.setdefault(product_id, {})
                report_dict[product_id]["product_name"] = product_name
                report_dict[product_id]["product_SKU_code"] = product_SKU_code
                report_dict[product_id]["category_id"] = category_id
                report_dict[product_id]["category_name"] = category_name

            report_dict[product_id].setdefault("variants", [])
            variant_batch_id = uuid.UUID(k.split(":")[0])
            warehouse_id = uuid.UUID(k.split(":")[1])
            product = {}
            # Lấy đầy đủ thông tin từng lô hàng
            batch_warehouses = count_import_export.get(variant_batch_id, {})
            product["variant_id"] = variant_id
            product["variant_name"] = variant_name
            product["variant_SKU_code"] = variant_SKU_code
            product["sale_price"] = variant_price

            inventory_first_obj = inventory_first.get(k, {})
            first_inventory = inventory_first_obj.get("quantity", 0)

            if not self.date_from or not inventory_first_obj.get("history_date") or inventory_first_obj.get("history_date") >= self.date_from:
                first_inventory = 0 if inventory_first_obj.get("history_type") == "+" else first_inventory

            variant_batches[variant_id].extend([
                {
                    "variant_batch_id": variant_batch_id,
                    "warehouse_id": batch_warehouse.get("warehouse_id"),
                    "warehouse_name": batch_warehouse.get("warehouse_name"),
                    "batch_name": batch_warehouse.get("batch_name"),
                    "expire_date": batch_warehouse.get("expire_date"),
                    "first_inventory": first_inventory,
                    "date_from": batch_warehouse.get("earliest_modified").date() if batch_warehouse.get("earliest_modified") else "",
                    "c_import": batch_warehouse.get("c_import", 0),
                    "c_export": batch_warehouse.get("c_export", 0),
                    "last_inventory": v.get("quantity", 0),
                    "date_to": batch_warehouse.get("latest_modified").date() if batch_warehouse.get("latest_modified") else "",
                }
                for batch_warehouse in batch_warehouses if batch_warehouse.get("warehouse_id") == warehouse_id
            ])
            product["batches"] = variant_batches[variant_id]
            report_dict[product_id]["variants"].append(product)
        return report_dict

    def reports(self) -> dict:
        report_dict = self.get_data_process_report()
        # Nhóm các lô hàng theo sản phẩm và sản phẩm biến thể
        report_list = []
        for id_product, values in report_dict.items():
            record = {}
            record["product_id"] = id_product
            record["product_name"] = values.get("product_name")
            record["product_SKU_code"] = values.get("product_SKU_code")
            record["category_id"] = values.get("category_id")
            record["category_name"] = values.get("category_name")
            record.setdefault("variants", [])
            variants = values.get("variants", [])

            product_first_inventory = 0
            product_c_import = 0
            product_c_export = 0
            product_last_inventory = 0

            check_duplicate_variant = []
            for variant_data in variants:
                if variant_data["variant_id"] in check_duplicate_variant:
                    continue
                
                check_duplicate_variant.append(variant_data["variant_id"])
                variant_first_number = 0
                variant_c_import = 0
                variant_c_export = 0
                variant_last_number = 0
                variant = variant_data

                batches = variant_data.get("batches", [])
                for batch in batches:
                    product_first_inventory += batch.get("first_inventory", 0)
                    product_last_inventory += batch.get("last_inventory", 0)
                    product_c_import += batch.get("c_import", 0)
                    product_c_export += batch.get("c_export", 0)

                    variant_first_number += batch.get("first_inventory", 0)
                    variant_last_number += batch.get("last_inventory", 0)
                    variant_c_import += batch.get("c_import", 0)
                    variant_c_export += batch.get("c_export", 0)
                variant["variant_first_inventory"] = variant_first_number
                variant["variant_last_inventory"] = variant_last_number
                variant["variant_c_import"] = variant_c_import
                variant["variant_c_export"] = variant_c_export
                record["variants"].append(variant)

            record["product_first_inventory"] = product_first_inventory
            record["product_last_inventory"] = product_last_inventory
            record["product_c_import"] = product_c_import
            record["product_c_export"] = product_c_export

            report_list.append(record)
        return report_list

def process_images(report_list: list) -> list:
    product_ids, variant_ids = set(), set() 
    for product in report_list:
        product_ids.add(product.get("product_id"))
        variants = product.get("variants", [])
        for variant in variants:
            variant_ids.add(variant.get("variant_id"))
    
    all_images = Images.objects.filter(
        Q(product_id__in=product_ids) | Q(product_variant_id__in=variant_ids)
    )

    product_images_list = defaultdict(list)
    variant_images_list = defaultdict(list)
    
    for image in all_images:
        if image.product_id:
            product_images_list[str(image.product_id)].append({"id": image.id, "image": IMAGE_BASE_URL + str(image.image), "is_default": image.is_default})
        if image.product_variant_id:
            variant_images_list[str(image.product_variant_id)].append({"id": image.id, "image": IMAGE_BASE_URL + str(image.image), "is_default": image.is_default})
    
    for product in report_list:
        product["images"] = product_images_list.get(str(product.get("product_id")), [])
        variants = product.get("variants", [])
        for variant in variants:
            variant["images"] = variant_images_list.get(str(variant.get("variant_id")), [])

    return report_list

def get_report_category_inventory(warehouse_ids, category_ids, date_from, date_to):
    date_from = (
        datetime.strptime(date_from, "%Y-%m-%d").date()
        if date_from
        else datetime.now().date()
    )
    date_to = (
        datetime.strptime(date_to, "%Y-%m-%d").date()
        if date_to
        else datetime.now().date()
    )

    if not category_ids:
        categories = ProductCategory.objects.values("id", "name")
    else:
        categories = ProductCategory.objects.filter(id__in=category_ids).values(
            "id", "name"
        )
    category_map = {category["name"]: category["id"] for category in categories}
    all_categories = list(category_map.keys())

    # Get all variants' initial quantities before the date_from
    query_initial_inventory = Q(history_date__date__lt=date_from)
    if warehouse_ids:
        query_initial_inventory.add(Q(warehouse_id__in=warehouse_ids), Q.AND)
    if category_ids:
        query_initial_inventory.add(
            Q(
                product_variant_batch__product_variant__product__category_id__in=category_ids
            ),
            Q.AND,
        )
    initial_inventory = (
        WarehouseInventory.history.filter(query_initial_inventory)
        .exclude(product_variant_batch__product_variant=None)
        .annotate(
            latest_date=Window(
                expression=Max("history_date"),
                partition_by=[F("product_variant_batch_id")],
            )
        )
        .filter(history_date=F("latest_date"))
        .values(
            "quantity",
            "product_variant_batch__product_variant__product__category__name",
            "product_variant_batch_id"  # Thêm trường này
        )
    )

    # Convert initial inventory to DataFrame với variant_id
    initial_inventory_df = pd.DataFrame(list(initial_inventory))
    initial_inventory_df = initial_inventory_df.rename(
        columns={
            "product_variant_batch__product_variant__product__category__name": "category",
            "product_variant_batch_id": "variant_id"
        }
    ) if not initial_inventory_df.empty else pd.DataFrame(columns=["category", "variant_id", "quantity"])

    # Fetch history records between date_from and date_to
    query_history_records = Q(
        history_date__date__gte=date_from,
        history_date__date__lte=date_to,
    )
    if warehouse_ids:
        query_history_records.add(Q(warehouse_id__in=warehouse_ids), Q.AND)
    if category_ids:
        query_history_records.add(
            Q(
                product_variant_batch__product_variant__product__category_id__in=category_ids
            ),
            Q.AND,
        )
    history_records = (
        WarehouseInventory.history.filter(query_history_records)
        .exclude(product_variant_batch__product_variant=None)
        .annotate(
            date=TruncDate("history_date"),
            row_number=Window(
                expression=RowNumber(),
                partition_by=[
                    F("date"),
                    F(
                        "product_variant_batch__product_variant__product__category__name"
                    ),
                    F("product_variant_batch_id"),
                ],
                order_by=F("history_date").desc(),
            ),
        )
        .filter(row_number=1)
        .values(
            "date",
            "quantity",
            "product_variant_batch__product_variant__product__category__name",
            "product_variant_batch_id"
        )
        .order_by("date")
    )

    # Convert history to DataFrame
    history_df = pd.DataFrame(list(history_records))
    if not history_df.empty:
        history_df = history_df.rename(
            columns={
                "product_variant_batch__product_variant__product__category__name": "category",
                "product_variant_batch_id": "variant_id"
            }
        )
    else:
        history_df = pd.DataFrame(columns=["date", "category", "variant_id", "quantity"])

    # Generate a full date range with categories
    date_range = pd.date_range(date_from, date_to, freq="D")
    
    # Tạo DataFrame kết quả
    result_data = []
    
    # Tạo dict để lưu trữ số lượng mới nhất của từng variant
    latest_quantities = {
        category: {
            variant_id: quantity 
            for variant_id, quantity in zip(
                initial_inventory_df[initial_inventory_df['category'] == category]['variant_id'],
                initial_inventory_df[initial_inventory_df['category'] == category]['quantity']
            )
        }
        for category in all_categories
    }

    # Xử lý từng ngày
    for date in date_range:
        date = date.date()
        for category in all_categories:
            # Cập nhật số lượng mới nhất cho các variant thay đổi trong ngày này
            day_changes = history_df[
                (history_df['date'] == date) & 
                (history_df['category'] == category)
            ]
            
            for _, change in day_changes.iterrows():
                latest_quantities[category][change['variant_id']] = change['quantity']
            
            # Tính tổng số lượng bằng cách cộng tất cả các số lượng mới nhất
            total_quantity = sum(latest_quantities[category].values())
            
            result_data.append({
                'date': date,
                'category': category,
                'total_quantity': total_quantity
            })
    
    # Convert to DataFrame for easier processing
    result_df = pd.DataFrame(result_data)
    
    # Format output
    result = []
    for date, group in result_df.groupby('date'):
        categories = [
            {
                'id': category_map[row['category']],
                'name': row['category'],
                'total_quantity': float(row['total_quantity']),
            }
            for _, row in group.iterrows()
        ]
        
        result.append({'date': date.strftime('%Y-%m-%d'), 'category': categories})

    return result