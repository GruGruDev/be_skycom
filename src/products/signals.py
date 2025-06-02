from django.db.models.signals import post_save
from django.dispatch import receiver

from products.models import ProductsVariantsBatches

@receiver(post_save, sender=ProductsVariantsBatches)
def check_default_batch(sender, instance: ProductsVariantsBatches, **kwargs):
    if instance.is_default:
        ProductsVariantsBatches.objects.exclude(
            id=instance.id
        ).filter(
            product_material=instance.product_material,
            product_variant=instance.product_variant
        ).update(is_default=False)
