# Generated by Django 5.0 on 2025-06-12 18:56

import django.db.models.deletion
import django.utils.timezone
import locations.models
import model_utils.fields
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('customers', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Districts',
            fields=[
                ('name', models.CharField(blank=True, max_length=64)),
                ('slug', models.CharField(max_length=64)),
                ('label', models.CharField(blank=True, max_length=256)),
                ('code', models.CharField(db_index=True, max_length=36, primary_key=True, serialize=False, unique=True)),
                ('ghn_province_id', models.IntegerField(null=True)),
                ('bd_province_id', models.CharField(max_length=256, null=True)),
                ('vtpost_province_id', models.CharField(max_length=256, null=True)),
                ('type', models.CharField(choices=[('quan', 'DISTRICT'), ('huyen', 'COUNTY'), ('thi-xa', 'TOWN'), ('thanh-pho', 'CITY')], default='tinh', max_length=64)),
                ('ghn_district_id', models.IntegerField(null=True)),
                ('bd_district_id', models.CharField(max_length=256, null=True)),
                ('vtpost_district_id', models.CharField(max_length=256, null=True)),
            ],
            options={
                'db_table': 'tbl_Districts',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Provinces',
            fields=[
                ('name', models.CharField(blank=True, max_length=64)),
                ('slug', models.CharField(max_length=64)),
                ('label', models.CharField(blank=True, max_length=256)),
                ('code', models.CharField(db_index=True, max_length=36, primary_key=True, serialize=False, unique=True)),
                ('ghn_province_id', models.IntegerField(null=True)),
                ('bd_province_id', models.CharField(max_length=256, null=True)),
                ('vtpost_province_id', models.CharField(max_length=256, null=True)),
                ('type', models.CharField(choices=[('thanh-pho', 'CITY'), ('tinh', 'PROVINCE')], default='tinh', max_length=64)),
            ],
            options={
                'db_table': 'tbl_Provinces',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Wards',
            fields=[
                ('name', models.CharField(blank=True, max_length=64)),
                ('slug', models.CharField(max_length=64)),
                ('label', models.CharField(blank=True, max_length=256)),
                ('code', models.CharField(db_index=True, max_length=36, primary_key=True, serialize=False, unique=True)),
                ('ghn_province_id', models.IntegerField(null=True)),
                ('bd_province_id', models.CharField(max_length=256, null=True)),
                ('vtpost_province_id', models.CharField(max_length=256, null=True)),
                ('type', models.CharField(choices=[('phuong', 'WARD'), ('xa', 'COMMUNE'), ('thi-tran', 'TOWN')], default='tinh', max_length=64)),
                ('ghn_district_id', models.IntegerField(null=True)),
                ('ghn_ward_id', models.CharField(max_length=16, null=True)),
                ('bd_district_id', models.CharField(max_length=256, null=True)),
                ('bd_ward_id', models.CharField(max_length=256, null=True)),
                ('vtpost_district_id', models.CharField(max_length=256, null=True)),
                ('vtpost_ward_id', models.CharField(max_length=256, null=True)),
            ],
            options={
                'db_table': 'tbl_Wards',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Address',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('id', model_utils.fields.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('type', models.CharField(choices=[('CT', 'CUSTOMER'), ('WH', 'WAREHOUSE'), ('OT', 'OTHER')], default=locations.models.AddressType['OTHER'], max_length=2)),
                ('note', models.TextField(blank=True, null=True)),
                ('address', models.CharField(max_length=1024)),
                ('is_default', models.BooleanField(default=False)),
                ('customer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='addresses', to='customers.customer')),
            ],
            options={
                'db_table': 'tbl_Addresses',
                'ordering': ['-created'],
            },
        ),
    ]
