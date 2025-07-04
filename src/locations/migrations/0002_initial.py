# Generated by Django 5.0 on 2025-06-12 18:56

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('locations', '0001_initial'),
        ('warehouses', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='address',
            name='warehouse',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='addresses', to='warehouses.warehouse'),
        ),
        migrations.AddField(
            model_name='districts',
            name='province',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='province_districts', to='locations.provinces'),
        ),
        migrations.AddField(
            model_name='wards',
            name='district',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='district_wards', to='locations.districts'),
        ),
        migrations.AddField(
            model_name='wards',
            name='province',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='province_wards', to='locations.provinces'),
        ),
        migrations.AddField(
            model_name='address',
            name='ward',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='addresses', to='locations.wards'),
        ),
    ]
