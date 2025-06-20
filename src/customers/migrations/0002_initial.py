# Generated by Django 5.0 on 2025-06-12 18:56

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('customers', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='customer_created', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='customer',
            name='customer_care_staff',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='customer_care_staff', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='customer',
            name='modified_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='customer_modified', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='customer',
            name='modified_care_staff_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='customer_care_staff_modified', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='customergroupdetail',
            name='customer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='customers.customer'),
        ),
        migrations.AddField(
            model_name='customergroupdetail',
            name='customer_group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='customers.customergroup'),
        ),
        migrations.AddField(
            model_name='customer',
            name='groups',
            field=models.ManyToManyField(through='customers.CustomerGroupDetail', to='customers.customergroup'),
        ),
        migrations.AddField(
            model_name='customerphone',
            name='customer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='phones', to='customers.customer'),
        ),
        migrations.AddField(
            model_name='customerrank',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='customer_rank_created', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='customerrank',
            name='modified_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='customer_rank_modified', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='customer',
            name='rank',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='object_rank', to='customers.customerrank'),
        ),
        migrations.AddField(
            model_name='customertagdetail',
            name='customer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='customers.customer'),
        ),
        migrations.AddField(
            model_name='customertagdetail',
            name='customer_tag',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='customers.customertag'),
        ),
        migrations.AddField(
            model_name='customer',
            name='tags',
            field=models.ManyToManyField(through='customers.CustomerTagDetail', to='customers.customertag'),
        ),
        migrations.AddField(
            model_name='historicalcustomer',
            name='created_by',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='historicalcustomer',
            name='customer_care_staff',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='historicalcustomer',
            name='history_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='historicalcustomer',
            name='modified_by',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='historicalcustomer',
            name='modified_care_staff_by',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='historicalcustomer',
            name='rank',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='customers.customerrank'),
        ),
        migrations.AddConstraint(
            model_name='customergroupdetail',
            constraint=models.UniqueConstraint(fields=('customer_group', 'customer'), name='unique_customer_group'),
        ),
        migrations.AddConstraint(
            model_name='customerphone',
            constraint=models.UniqueConstraint(fields=('customer', 'phone'), name='unique_customer_phone'),
        ),
        migrations.AlterUniqueTogether(
            name='customerrank',
            unique_together={('spend_from', 'spend_to')},
        ),
        migrations.AddConstraint(
            model_name='customertagdetail',
            constraint=models.UniqueConstraint(fields=('customer_tag', 'customer'), name='unique_customer_tag'),
        ),
    ]
