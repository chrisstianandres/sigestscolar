# Generated by Django 3.2.8 on 2022-01-28 17:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('empresa', '0004_auto_20220128_1148'),
    ]

    operations = [
        migrations.AlterField(
            model_name='empresa',
            name='descripcioncorta',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Descripcion corta'),
        ),
    ]