# Generated by Django 3.2.8 on 2021-12-25 00:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('factura', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='factura',
            name='estado',
            field=models.IntegerField(choices=[(2, 'INCORRECTA'), (3, 'ANULADA'), (1, 'CORRECTA')], default=1, verbose_name='Estado Factura'),
        ),
    ]