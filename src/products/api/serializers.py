import ast

from rest_framework import serializers
from rest_framework import exceptions

from core.validators import validate_min_max
from files.api.serializers import ImagesReadBaseSerializer
from products.enums import ProductVariantType
from products.models import ProductCategory
from products.models import Products
from products.models import ProductsMaterials
from products.models import ProductSupplier
from products.models import ProductsVariants
from products.models import ProductsVariantsBatches
from products.models import ProductsVariantsComboDetail
from products.models import ProductsVariantsMapping
from products.models import ProductsVariantsMaterials
from products.models import ProductTag
from products.reports import ProductReportPivot
from utils.reports import BindingExprEnum
from users.utils import has_custom_permission # Import hàm mới

# ... (Giữ nguyên các serializer từ CategorySerializer đến ProductVariantReadMaterialBaseSerializer) ...
class CategorySerializer(serializers.ModelSerializer):
    total_products = serializers.IntegerField(read_only=True)
    total_inventory = serializers.IntegerField(read_only=True)

    class Meta:
        model = ProductCategory
        fields = "__all__"
        extra_kwargs = {"name": {"required": True}, "code": {"required": True}}


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductTag
        fields = "__all__"


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSupplier
        fields = "__all__"
        extra_kwargs = {"name": {"required": True}}


class SupplierPatchUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSupplier
        fields = (
            "business_code",
            "tax_number",
            "country",
            "address",
            "status",
            "legal_representative",
            "established_at",
        )


class ProductVariantComboDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductsVariantsComboDetail
        fields = "__all__"


class ProductVariantComboDetailCreateSerializer(serializers.ModelSerializer):
    detail_variant_id = serializers.UUIDField()
    price_detail_variant = serializers.IntegerField(required=True)

    def validate_detail_variant_id(self, attr):
        if not ProductsVariants.objects.filter(
            id=attr, type=ProductVariantType.SIMPLE.value
        ):
            raise serializers.ValidationError(
                f"Variant {attr} does not exist, or the type of variant must be simple"
            )
        return attr

    class Meta:
        model = ProductsVariantsComboDetail
        fields = ("detail_variant_id", "price_detail_variant", "quantity")
        extra_kwargs = {
            "origin_variant": {"required": False},
            "price_detail_variant": {"required": True},
            "quantity": {"required": True},
        }


class ProductVariantCreateMaterialSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    quantity = serializers.IntegerField(required=False)
    weight = serializers.DecimalField(
        max_digits=15, decimal_places=4, coerce_to_string=False
    )


class ProductVariantReadMaterialBaseSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="product_material.id")
    name = serializers.CharField(source="product_material.name")
    SKU_code = serializers.CharField(source="product_material.SKU_code")
    weight = serializers.DecimalField(
        max_digits=15, decimal_places=4, coerce_to_string=False
    )

    class Meta:
        model = ProductsVariantsMaterials
        fields = ("id", "name", "SKU_code", "quantity", "weight")


class ProductVariantsSerializer(serializers.ModelSerializer):
    images = ImagesReadBaseSerializer(many=True, read_only=True)

    class Meta:
        model = ProductsVariants
        exclude = ("tags",)
        extra_kwargs = {
            "created_by": {"read_only": True},
            "modified_by": {"read_only": True},
        }

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        request = self.context.get("request")

        if request and hasattr(request, "user") and request.user.is_authenticated:
            user = request.user
            # Thay thế user.has_perm bằng hàm kiểm tra tùy chỉnh
            if not has_custom_permission(user, "products.view_variant_image"):
                ret.pop("images", None)
        else:
            # Nếu không xác thực được user, mặc định ẩn ảnh
            ret.pop("images", None)

        return ret


# ... (Giữ nguyên các serializer từ ProductVariantCreateSerializer đến ProductVariantComboDetailRetrieveSerializer) ...
class ProductVariantCreateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=ProductTag.objects.all(), required=False
    )
    combo_variants = ProductVariantComboDetailCreateSerializer(
        many=True, required=False
    )
    sale_price = serializers.IntegerField(required=True)
    materials = ProductVariantCreateMaterialSerializer(many=True, required=False)

    def validate(self, attrs):
        commission = attrs.get("commission")
        if commission:
            validate_min_max(commission, 0)
            attrs["commission_percent"] = None

        commission_percent = attrs.get("commission_percent")
        if commission_percent:
            validate_min_max(commission_percent, 0, 100)
            attrs["commission"] = None

        self._validate_combo_variants(attrs)
        return super().validate(attrs)

    def _validate_combo_variants(self, attrs):
        variant_type = attrs.get("type")
        if variant_type in [ProductVariantType.BUNDLE, ProductVariantType.COMBO]:
            combo_variants = attrs.get("combo_variants", [])
            if len(combo_variants) < 2:
                raise serializers.ValidationError(
                    {"combo_variants": ["Combo or Bundle must have 2 or more"]}
                )
            sale_price = attrs.get("sale_price", 0)
            variant_details_price = sum(
                variant_d.get("price_detail_variant", 0) * variant_d.get("quantity", 0)
                for variant_d in combo_variants
            )
            if sale_price != variant_details_price:
                raise serializers.ValidationError(
                    {
                        "combo_variants": [
                            "The price of the combo or bundle must be equal to the total price of the items inside"
                        ]
                    }
                )

    class Meta:
        model = ProductsVariants
        exclude = ("product",)
        extra_kwargs = {
            "product": {"required": False},
            "combo_variants": {"required": False},
            "created_by": {"read_only": True},
            "modified_by": {"read_only": True},
        }


class ProductVariantCreateSingleSerializer(ProductVariantCreateSerializer):
    product_id = serializers.UUIDField(required=True)
    inventory_quantity = serializers.IntegerField(min_value=0, required=False)
    inventory_note = serializers.CharField(allow_null=True, allow_blank=True, required=False)

    class Meta:
        model = ProductVariantCreateSerializer.Meta.model
        exclude = ("product",)
        extra_kwargs = {
            "combo_variants": {"required": False},
            "created_by": {"read_only": True},
            "modified_by": {"read_only": True},
            "sale_price": {"required": True},
        }


class ProductVariantBulkCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductsVariants
        fields = "__all__"
        extra_kwargs = {
            "type": {"read_only": True},
            "modified_by": {"read_only": True},
            "created_by": {"read_only": True},
        }


class ProductVariantUpdateSerializer(ProductVariantCreateSerializer):
    materials = ProductVariantCreateMaterialSerializer(many=True, required=False)

    class Meta:
        model = ProductsVariants
        fields = "__all__"
        extra_kwargs = {
            "created_by": {"read_only": True},
            "modified_by": {"read_only": True},
            "product": {"read_only": True},
            "type": {"read_only": True},
        }

    def validate_sale_price(self, attr):
        if self.instance.type in [ProductVariantType.BUNDLE, ProductVariantType.COMBO]:
            raise serializers.ValidationError(
                "Can't update the sale_price of variant combo or bundle"
            )
        return attr


class ProductVariantComboDetailRetrieveSerializer(serializers.ModelSerializer):
    detail_variant = ProductVariantsSerializer()

    class Meta:
        model = ProductsVariantsComboDetail
        fields = "__all__"


class ProductVariantRetrieveSerializer(serializers.ModelSerializer):
    images = ImagesReadBaseSerializer(many=True, read_only=True)
    total_inventory = serializers.SerializerMethodField(read_only=True)
    total_weight = serializers.SerializerMethodField(read_only=True)
    materials = ProductVariantReadMaterialBaseSerializer(many=True, read_only=True)
    category_name = serializers.CharField(read_only=True)

    class Meta:
        model = ProductsVariants
        exclude = ("tags",)

    def get_total_inventory(self, obj):
        try:
            return obj.total_inventory
        except Exception:
            batches = getattr(obj, "batches")
            total_quantity = 0
            if batches:
                for batch in batches.all():
                    if hasattr(batch, "warehouse_inventory_product_variant_batch"):
                        quantity = sum(
                            i.quantity
                            for i in batch.warehouse_inventory_product_variant_batch.all()
                        )
                        total_quantity += quantity
            return total_quantity

    def get_total_weight(self, obj):
        try:
            return obj.total_weight
        except Exception:
            return sum(material.weight for material in obj.materials.all())

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        request = self.context.get("request")

        if request and hasattr(request, "user") and request.user.is_authenticated:
            user = request.user
            # Thay thế user.has_perm bằng hàm kiểm tra tùy chỉnh
            if not has_custom_permission(user, "products.view_variant_image"):
                ret.pop("images", None)
        else:
            ret.pop("images", None)

        ret["total_material_quantity"] = len(ret.get("materials", []))
        return ret


# ... (Giữ nguyên phần còn lại của file) ...
class ProductMaterialReadVariantBaseSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="product_variant.id")
    name = serializers.CharField(source="product_variant.name")
    SKU_code = serializers.CharField(source="product_variant.SKU_code")

    class Meta:
        model = ProductsVariantsMaterials
        fields = (
            "id",
            "name",
            "SKU_code",
        )

class ProductMaterialReadBaseSerializer(serializers.ModelSerializer):
    images = ImagesReadBaseSerializer(many=True, read_only=True)

    class Meta:
        model = ProductsMaterials
        fields = ("id", "SKU_code", "name", "images")

class ProductMaterialSerializer(serializers.ModelSerializer):
    images = ImagesReadBaseSerializer(many=True, read_only=True)
    total_inventory = serializers.SerializerMethodField(read_only=True)
    variants = ProductMaterialReadVariantBaseSerializer(many=True, read_only=True)
    weight = serializers.DecimalField(
        max_digits=15, decimal_places=4, coerce_to_string=False, required=False
    )
    length = serializers.DecimalField(
        max_digits=15, decimal_places=4, coerce_to_string=False, required=False
    )
    height = serializers.DecimalField(
        max_digits=15, decimal_places=4, coerce_to_string=False, required=False
    )
    width = serializers.DecimalField(
        max_digits=15, decimal_places=4, coerce_to_string=False, required=False
    )

    class Meta:
        model = ProductsMaterials
        fields = "__all__"
        extra_kwargs = {
            "created_by": {"read_only": True},
            "modified_by": {"read_only": True},
        }

    def get_total_inventory(self, obj):
        batches = getattr(obj, "batches")
        total_quantity = 0
        if batches:
            for batch in batches.all():
                if hasattr(batch, "warehouse_inventory_product_variant_batch"):
                    quantity = sum(
                        i.quantity
                        for i in batch.warehouse_inventory_product_variant_batch.all()
                    )
                    total_quantity += quantity
        return total_quantity

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        if request and "variant" in request.GET:
            data.pop("variants", None)
        return data


class ProductMaterialVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductsVariantsMaterials
        fields = "__all__"


class ProductVariantBatchSerializer(serializers.ModelSerializer):
    product_variant = ProductVariantsSerializer()
    product_material = ProductMaterialReadBaseSerializer()

    class Meta:
        model = ProductsVariantsBatches
        fields = "__all__"


class ProductVariantBatchCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductsVariantsBatches
        fields = "__all__"


class ProductVariantBatchUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductsVariantsBatches
        fields = ("name", "expire_date", "is_default")

    def validate(self, attrs):
        if attrs.get("is_default") is False:
            raise exceptions.ValidationError({"is_default": "Trường này không thể là Flase"})
        return super().validate(attrs)


class ProductVariantMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductsVariantsMapping
        fields = "__all__"


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Products
        fields = "__all__"
        extra_kwargs = {
            "created_by": {"read_only": True},
            "modified_by": {"read_only": True},
        }


class ProductListSerializer(serializers.ModelSerializer):
    variants = ProductVariantRetrieveSerializer(many=True, read_only=True)
    images = ImagesReadBaseSerializer(many=True)
    total_variants = serializers.IntegerField(read_only=True)
    total_inventory = serializers.IntegerField(read_only=True)

    class Meta:
        model = Products
        fields = "__all__"


class ProductRetrieveSerializer(serializers.ModelSerializer):
    variants = ProductVariantRetrieveSerializer(many=True, read_only=True)
    category = CategorySerializer(required=False)
    supplier = SupplierSerializer(required=False)
    images = ImagesReadBaseSerializer(many=True)

    class Meta:
        model = Products
        fields = "__all__"


class ProductCreateSerializer(serializers.ModelSerializer):
    variants = ProductVariantCreateSerializer(
        many=True, required=True, allow_empty=False
    )
    category = serializers.PrimaryKeyRelatedField(
        queryset=ProductCategory.objects.all(), required=True
    )
    supplier = serializers.PrimaryKeyRelatedField(
        queryset=ProductSupplier.objects.all(), required=False
    )

    class Meta:
        model = Products
        fields = (
            "name",
            "note",
            "is_active",
            "category",
            "supplier",
            "variants",
            "SKU_code",
        )


class ProductCreateWtVariantSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=ProductCategory.objects.all(), required=True
    )
    supplier = serializers.PrimaryKeyRelatedField(
        queryset=ProductSupplier.objects.all(), required=False
    )

    class Meta:
        model = Products
        fields = (
            "id",
            "name",
            "note",
            "is_active",
            "category",
            "supplier",
            "created_by",
        )
        extra_kwargs = {"id": {"read_only": True}}


class ProductVariantPromotionDisplaySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductsVariants
        fields = "__all__"


class ProductReportPivotParams(serializers.Serializer):
    dimensions = serializers.CharField(help_text=ProductReportPivot.help_text_dims())
    metrics = serializers.CharField(help_text=ProductReportPivot.help_text_metrics())
    filters = serializers.CharField(
        help_text=ProductReportPivot.help_text_filters(),
        allow_null=True,
        required=False,
    )
    b_expr_dims = serializers.ChoiceField(
        choices=BindingExprEnum.choices(), default=BindingExprEnum.AND, required=False
    )
    b_expr_metrics = serializers.ChoiceField(
        choices=BindingExprEnum.choices(), default=BindingExprEnum.AND, required=False
    )

    def validate_dimensions(self, value):
        try:
            value_list = ast.literal_eval(value)
            for v in value_list:
                if v not in ProductReportPivot.DIMS_AVB:
                    raise ValueError("%s not implemented yet" % v)
            return value_list
        except (ValueError, Exception) as err:
            raise serializers.ValidationError("Dimensions invalid: %s" % str(err))

    def validate_metrics(self, value):
        try:
            value_list = ast.literal_eval(value)
            for v in value_list:
                if v not in ProductReportPivot.METRICS_AVB:
                    raise ValueError("%s not implemented yet" % v)
            return value_list
        except (ValueError, Exception) as err:
            raise serializers.ValidationError("Metrics invalid: %s" % str(err))

    def validate_filters(self, value):
        try:
            return ast.literal_eval(value)
        except (ValueError, Exception) as err:
            raise serializers.ValidationError("Filters invalid: %s" % str(err))

    def validate_ft_bind_expr(self, value):
        return value or BindingExprEnum.AND


class ResultProductPivotResponse(serializers.Serializer):
    created_date = serializers.DateField(help_text="Ngày cơm")
    created_by__id = serializers.UUIDField(help_text="ID người tạo sản phẩm")
    created_by__name = serializers.CharField(help_text="Tên người tạo sản phẩm")
    SKU_code = serializers.CharField(help_text="Mã sản phẩm")
    name = serializers.CharField(help_text="Tên sản phẩm")
    warehouse_id = serializers.CharField(help_text="Mã kho")
    warehouse_name = serializers.CharField(help_text="Tên kho")
    batches__id = serializers.CharField(help_text="Mã lô hàng")
    batches__name = serializers.CharField(help_text="Tên lô hàng")
    sheet_type = serializers.CharField(help_text="Loại sheet")
    total_revenue = serializers.FloatField(help_text="Total Revenue")
    total_actual_revenue = serializers.FloatField(
        help_text="Actual Revenue: Total value of goods sold after subtracting discounts"
    )
    total_promotion_amount = serializers.FloatField(
        help_text="Total Promotion Amount: Total amount of promotion for the corresponding product"
    )
    quantity_sold = serializers.FloatField(
        help_text="Quantity Sold: Quantity of products that appear in successfully delivered orders"
    )
    actual_quantity_sold = serializers.FloatField(
        help_text="Actual Quantity Sold: Quantity of products actually sold (excluding returns)"
    )
    number_of_orders = serializers.FloatField(
        help_text="Number of Orders: Number of orders containing the product"
    )
    inventory_quantity = serializers.FloatField(help_text="Inventory Quantity")
    quantity_import = serializers.FloatField(help_text="Quantity Purchased")
    quantity_export = serializers.FloatField(help_text="Quantity Sold Out")
    quantity = serializers.FloatField(help_text="Quantity of product in sheet")


class ProductReportPivotResponse(serializers.Serializer):
    count = serializers.IntegerField()
    results = ResultProductPivotResponse(many=True)


class ImportProductVariantSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name")
    product_SKU_code = serializers.CharField(source="product.SKU_code")
    product_category = serializers.CharField(source="product.category.name")
    inventory_quantity = serializers.FloatField(
        source="batches.warehouse_inventory_product_variant_batch.quantity"
    )

    class Meta:
        model = ProductsVariants
        fields = [
            "product_name",
            "product_SKU_code",
            "product_category",
            "name",
            "SKU_code",
            "sale_price",
            "neo_price",
            "note",
            "inventory_quantity",
        ]

    SKU_code = serializers.CharField()

    def validate(self, attrs):
        existing_sku = self.context.get("existing_sku", set())
        existing_products = self.context.get("existing_products", {})

        errors = {}
        product_data = attrs.pop("product")
        category_name = product_data["category"]["name"]
        product_sku = product_data.get("SKU_code")
        if attrs["SKU_code"] in existing_sku:
            errors["SKU_code"] = [
                f"Biến thể có mã SKU {attrs['SKU_code']} đã tồn tại hoặc bị trùng lặp."
            ]
        existing_sku.add(attrs["SKU_code"])

        product = existing_products.get(product_sku)
        if product.category.name != category_name:
            errors["product_category"] = [
                f"Sản phẩm có mã SKU {product.SKU_code} không chứa danh mục {category_name}"
            ]

        if errors:
            raise serializers.ValidationError(errors)

        attrs["product"] = product
        attrs["bar_code"] = product.SKU_code
        return attrs


class ProductVariantRevenueSerializer(serializers.ModelSerializer):
    images = ImagesReadBaseSerializer(many=True, read_only=True)
    inventory_quantity = serializers.SerializerMethodField()
    sold_quantity = serializers.SerializerMethodField()
    revenue = serializers.SerializerMethodField()

    class Meta:
        model = ProductsVariants
        fields = (
            "id",
            "SKU_code",
            "bar_code",
            "name",
            "images",
            "inventory_quantity",
            "sold_quantity",
            "revenue",
            "sale_price",
            "neo_price",
        )

    def get_inventory_quantity(self, obj):
        return obj.inventory_quantity

    def get_sold_quantity(self, obj):
        return obj.sold_quantity

    def get_revenue(self, obj):
        return obj.revenue


class BulkUpdateProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductsVariants
        fields = [
            "SKU_code",
            "sale_price",
            "neo_price",
        ]

    SKU_code = serializers.CharField()

    def validate(self, attrs):
        existing_sku = self.context.get("existing_sku", set())

        errors = {}
        if attrs["SKU_code"] not in existing_sku:
            errors["SKU_code"] = [
                f"Biến thể có mã SKU {attrs['SKU_code']} không tồn tại trong hệ thống."
            ]
        existing_sku.add(attrs["SKU_code"])


        if errors:
            raise serializers.ValidationError(errors)

        return attrs