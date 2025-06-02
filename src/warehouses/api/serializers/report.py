from rest_framework import serializers

class ImagesBase(serializers.Serializer):
    id = serializers.CharField()
    image = serializers.CharField()

class ReportWarehouseBatches(serializers.Serializer):
    variant_batch_id = serializers.CharField()
    warehouse_id = serializers.CharField()
    warehouse_name = serializers.CharField()
    batch_name = serializers.CharField()
    expire_date = serializers.DateField()
    first_inventory = serializers.DecimalField(max_digits=15, decimal_places=4)
    date_from = serializers.DateField()
    c_import = serializers.DecimalField(max_digits=15, decimal_places=4)
    c_export = serializers.DecimalField(max_digits=15, decimal_places=4)
    last_inventory = serializers.DecimalField(max_digits=15, decimal_places=4)
    date_to = serializers.DateField()


class ReportWarehouseVariant(serializers.Serializer):
    variant_id = serializers.CharField()
    variant_name = serializers.CharField()
    variant_SKU_code = serializers.CharField()
    variant_first_inventory = serializers.DecimalField(max_digits=15, decimal_places=4)
    variant_last_inventory = serializers.DecimalField(max_digits=15, decimal_places=4)
    variant_c_import = serializers.DecimalField(max_digits=15, decimal_places=4)
    variant_c_export = serializers.DecimalField(max_digits=15, decimal_places=4)
    neo_price = serializers.DecimalField(max_digits=20, decimal_places=2, required=False)
    sale_price = serializers.DecimalField(max_digits=20, decimal_places=2, required=False)
    batches = ReportWarehouseBatches(many=True)
    images = ImagesBase(many=True, required=False)

class ReportWarehouseSerializer(serializers.Serializer):
    product_id = serializers.CharField()
    product_name = serializers.CharField()
    product_SKU_code = serializers.CharField()
    category_id = serializers.CharField()
    category_name = serializers.CharField()
    product_first_inventory = serializers.DecimalField(max_digits=15, decimal_places=4)
    product_last_inventory = serializers.DecimalField(max_digits=15, decimal_places=4)
    product_c_import = serializers.DecimalField(max_digits=15, decimal_places=4)
    product_c_export = serializers.DecimalField(max_digits=15, decimal_places=4)
    variants = ReportWarehouseVariant(many=True)
    images = ImagesBase(many=True, required=False)