# Generated by Django 3.2.8 on 2022-01-28 16:43

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('producto', '0006_alter_inventario_fechaingreso'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventario',
            name='fechaingreso',
            field=models.DateField(default=datetime.datetime(2022, 1, 28, 11, 43, 53, 580986)),
        ),
    ]