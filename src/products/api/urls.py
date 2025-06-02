from django.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter

from products.api.views import BulkUpdateProductVariantsView
from products.api.views import CategoryViewset
from products.api.views import ProductMaterialVariantViewset
from products.api.views import ProductMaterialViewset
from products.api.views import ProductReportListAPIView
from products.api.views import ProductSupplierViewset
from products.api.views import ProductVariantBatchViewset
from products.api.views import ProductVariantMappingViewset
from products.api.views import ProductVariantViewset
from products.api.views import ProductViewset
from products.api.views import TagViewset
from products.api.views import ProductVariantRevenueView
from products.api.views import ImportProductVariantsView


router = DefaultRouter()
router.register("category", CategoryViewset, basename="product_category")
router.register("tag", TagViewset, basename="product_tag")
router.register("supplier", ProductSupplierViewset, basename="product_supplier")
router.register("mapping", ProductVariantMappingViewset, basename="product_variant_mapping")
router.register("variants", ProductVariantViewset, basename="product_variant")
router.register("materials", ProductMaterialViewset, basename="product_material")
router.register("variants-materials", ProductMaterialVariantViewset, basename="product_variant_material")
router.register("batches", ProductVariantBatchViewset, basename="product_variant_batch")
router.register("", ProductViewset, basename="product")


urlpatterns = [
    path("report/pivot", ProductReportListAPIView.as_view(), name="product_report"),
    path("variants/revenue", ProductVariantRevenueView.as_view(), name="product_variant_revenue"),
    path("variants/import", ImportProductVariantsView.as_view(), name="import_product_variants"),
    path("variants/bulk-update/", BulkUpdateProductVariantsView.as_view(), name="bulk_update_product_variants"),
] + router.urls
