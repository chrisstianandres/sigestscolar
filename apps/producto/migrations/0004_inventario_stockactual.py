# Generated by Django 3.2.8 on 2022-01-28 15:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('producto', '0003_producto_valor'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventario',
            name='stockactual',
            field=models.IntegerField(default=0),
        ),
    ]
