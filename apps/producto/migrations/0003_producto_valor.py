# Generated by Django 3.2.8 on 2022-01-18 02:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('producto', '0002_auto_20220117_2041'),
    ]

    operations = [
        migrations.AddField(
            model_name='producto',
            name='valor',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=30, verbose_name='Valor'),
        ),
    ]