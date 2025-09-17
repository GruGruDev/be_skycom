from files.models import ImageTypes

CONVERT_APP_LABEL = {
    "customers": "CUSTOMERS",
    "users": "USERS",
    "locations": "LOCATIONS",
    "leads": "LEADS",
    "products": "PRODUCTS",
    "promotions": "PROMOTIONS",
    "warehouses": "WAREHOUSES",
    "orders": "ORDERS",
    "delivery": "DELIVERY",
    "files": "FILES",
}


ACTION_TYPES_NAME = {
    "Create": "Tạo mới",
    "Read": "Xem",
    "Update": "Cập nhật",
    "Delete": "Xóa",
    "Export": "Xuất file",
    "Import": "Nhập file",
    "Login": "Đăng nhập",
    "Logout": "Đăng xuất",
}


MODEL_FIELDS_MAP = {
    "User": ["name", "email"],
    "Customer": ["name", "phone", "customer_code"],
    "CustomerGroup": ["name"],
    "CustomerGroupDetail": ["customer", "customer_group"],
    "Orders": ["order_key", "customer__name", "price_total_order_actual"],
    "OrdersPayments": ["order", "type", "price_from_order"],
    "Lead": ["name", "phone"],
    "Department": ["name"],
    "Address": ["address"],
    "PromotionOrder": ["name", "price_value", "percent_value"],
    "PromotionVariant": ["name", "price_value", "percent_value"],
    "PromotionVoucher": ["name", "price_value", "percent_value"],
    "ProductCategory": ["name"],
    "Products": ["name"],
    "ProductsVariantsBatches": ["name", "expiry_date"],
    "ProductsVariants": ["SKU_code", "name", "sale_price"],
    "ProductsMaterials": ["SKU_code", "name", "sale_price"],
    "Warehouse": ["name"],
    "WarehouseInventoryAvailable": ["quantity", "product_variant_batches", "warehouse"],
    # "WarehouseInventoryLog"
    # "WarehouseInventoryReason"
    "WarehouseSheetCheckDetail": ["sheet__code", "sheet__warehouse", "product_variant_batch", "quantity_system", "quantity_actual"]
    # "Warehouse"
    # "DeliveryCompany"
    # Thêm các model khác tại đây
}

MODEL_MESSAGE_FORMATS = {
    "Lead": "{action} lead tên: {name}, số điện thoại: {phone}",
    "User": "{action} người dùng tên: {name}, email: {email}",
    "Customer": "{action} khách hàng tên: {name}, số điện thoại: {phone}, mã khách hàng: {customer_code}",
    "CustomerGroup": "{action} nhóm khách hàng tên: {name}",
    "CustomerGroupDetail": "{action} khách hàng: {customer} ở nhóm khách hàng: {customer_group}",
    "Orders": "{action} đơn hàng mã: {order_key}, khách hàng {customer__name}, giá trị {price_total_order_actual}",
    "OrdersPayment": "{action} thanh toán đơn hàng mã: {order}, loại: {type}, giá trị: {price_from_order}",
    "ProductCategory": "{action} danh mục sản phẩm tên: {name}",
    "Products": "{action} sản phẩm tên: {name}",
    "ProductsVariants": "{action} biến thể sản phẩm mã: {SKU_code}, tên: {name}, giá bán {sale_price}",
    "ProductsMaterials": "{action} nguyên liệu mã: {SKU_code}, tên: {name}, giá bán {sale_price}",
    "ProductsVariantsBatches": "{action} lô tên: {name}, ngày hết hạn: {expiry_date}",
    "PromotionOrder": "{action} khuyến mãi đơn hàng tên: {name}, giá trị: {price_value}, phần trăm: {percent_value}",
    "PromotionVariant": "{action} khuyến mãi sản phẩm tên: {name}, giá trị: {price_value}, phần trăm: {percent_value}",
    "PromotionVoucher": "{action} khuyến mãi voucher tên: {name}, giá trị: {price_value}, phần trăm: {percent_value}",
    "Warehouse": "{action} kho tên: {name}",
    "WarehouseInventoryAvailable": "{action} số lượng: {quantity}, lô biến thể sản phẩm: {product_variant_batches}, " "kho: {warehouse}",
    "WarehouseSheetCheckDetail": "{action} chi tiết phiếu kiểm: {sheet__code}, kho: {sheet__warehouse}, "
    "lô biến thể sản phẩm: {product_variant_batch}, số lượng hệ thống: {quantity_system}, "
    "số lượng thực tế: {quantity_actual}",
    "Images": "{action} ảnh cho {object_type} {object_name}",
}


def get_nested_attr(obj, attr_path, default=None):
    attrs = attr_path.split("__")  # Tách các cấp bởi dấu '__'
    for attr in attrs:
        obj = getattr(obj, attr, default)  # Lấy thuộc tính của đối tượng
        if obj is None:  # Nếu bất kỳ cấp nào không tồn tại, trả về giá trị mặc định
            return default
    return obj


# xử lí Object Type Image
def get_image_related_field(image_instance):
    field_mapping = {
        ImageTypes.PRODUCT.value: "product",
        ImageTypes.PRODUCT_VARIANT.value: "product_variant",
        ImageTypes.USER.value: "user",
        ImageTypes.PAYMENT.value: "payment",
        ImageTypes.MATERIAL.value: "material",
        # ImageTypes.ORDER.value: "order",
        ImageTypes.OTHER.value: None,
    }

    object_type_name_mapping = {
        ImageTypes.PRODUCT.value: "sản phẩm",
        ImageTypes.PRODUCT_VARIANT.value: "biến thể",
        ImageTypes.USER.value: "người dùng",
        ImageTypes.PAYMENT.value: "giao dịch",
        ImageTypes.MATERIAL.value: "nguyên liệu",
        # ImageTypes.ORDER.value: "đơn hàng",
        ImageTypes.OTHER.value: "khác",
    }

    # Lấy giá trị field dựa trên `type`
    object_type = object_type_name_mapping.get(image_instance.type)
    related_field = field_mapping.get(image_instance.type)

    # Trả về giá trị field hoặc None nếu không có field tương ứng
    if related_field:
        object_name = getattr(getattr(image_instance, related_field, None), "name", None)
        return {"object_type": object_type, "object_name": object_name}
    return {"object_type": object_type, "object_name": None}


def get_fields_for_model(model_name, instance):
    fields = MODEL_FIELDS_MAP.get(model_name, [])
    if model_name == "Images":
        return get_image_related_field(instance)
    return {field: get_nested_attr(instance, field, None) for field in fields}


def create_message(action_type, model_name, instance):
    fields = get_fields_for_model(model_name, instance)
    action = ACTION_TYPES_NAME.get(action_type)
    fields["action"] = action

    format_string = MODEL_MESSAGE_FORMATS.get(model_name)
    if format_string is not None:
        return format_string.format(**fields)
    return None


def get_action_name(app_label):
    return CONVERT_APP_LABEL.get(app_label, app_label)

# =================================================================
# HÀM KIỂM TRA QUYỀN MỚI ĐƯỢC THÊM VÀO
# =================================================================
def has_custom_permission(user, perm_codename):
    """
    Kiểm tra quyền của người dùng dựa trên trường JSON `data` của Role.
    """
    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    if not hasattr(user, 'role') or user.role is None or not isinstance(user.role.data, dict):
        return False

    role_data = user.role.data
    
    # Tách codename thành app_label và action, vd: "products.view_variant_image"
    # perm_parts = perm_codename.split('.')
    # if len(perm_parts) != 2:
    #     return False
    # app_label, action = perm_parts

    # if app_label in role_data and isinstance(role_data[app_label], dict):
    #     if action in role_data[app_label]:
    #         return True

    for group, perms in role_data.items():
      if isinstance(perms, dict) and perm_codename in perms:
        return True

    return False