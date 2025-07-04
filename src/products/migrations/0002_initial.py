# Generated by Django 5.0 on 2025-06-12 18:56

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('products', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='products',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='product_create', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='products',
            name='modified_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='product_modify', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='productsmaterials',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='product_materials_create', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='productsmaterials',
            name='modified_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='product_materials_update', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='products',
            name='supplier',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products', to='products.productsupplier'),
        ),
        migrations.AddField(
            model_name='productsvariants',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='product_variants_create', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='productsvariants',
            name='modified_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='product_variants_update', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='productsvariants',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variants', to='products.products'),
        ),
        migrations.AddField(
            model_name='productsvariantsbatches',
            name='product_material',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='batches', to='products.productsmaterials'),
        ),
        migrations.AddField(
            model_name='productsvariantsbatches',
            name='product_variant',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='batches', to='products.productsvariants'),
        ),
        migrations.AddField(
            model_name='productsvariantscombodetail',
            name='detail_variant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='combos', to='products.productsvariants'),
        ),
        migrations.AddField(
            model_name='productsvariantscombodetail',
            name='origin_variant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='combo_variants', to='products.productsvariants'),
        ),
        migrations.AddField(
            model_name='productsvariantsmapping',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='product_mapping_create', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='productsvariantsmapping',
            name='modified_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='product_mapping_update', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='productsvariantsmapping',
            name='product_variant',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='mappings', to='products.productsvariants'),
        ),
        migrations.AddField(
            model_name='productsvariantsmaterials',
            name='product_material',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variants', to='products.productsmaterials'),
        ),
        migrations.AddField(
            model_name='productsvariantsmaterials',
            name='product_variant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='materials', to='products.productsvariants'),
        ),
        migrations.AddField(
            model_name='productsvariants',
            name='tags',
            field=models.ManyToManyField(blank=True, related_name='product_variant_tags', to='products.producttag'),
        ),
        migrations.AlterUniqueTogether(
            name='productsvariantsbatches',
            unique_together={('product_variant', 'name')},
        ),
        migrations.AlterUniqueTogether(
            name='productsvariantsmapping',
            unique_together={('third_product_id', 'product_variant')},
        ),
    ]
