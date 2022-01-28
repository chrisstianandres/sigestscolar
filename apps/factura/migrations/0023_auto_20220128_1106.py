# Generated by Django 3.2.8 on 2022-01-28 16:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('factura', '0022_auto_20220128_1018'),
    ]

    operations = [
        migrations.AlterField(
            model_name='factura',
            name='estado',
            field=models.IntegerField(choices=[(2, 'INCORRECTA'), (1, 'CORRECTA'), (3, 'ANULADA')], default=1, verbose_name='Estado Factura'),
        ),
        migrations.AlterField(
            model_name='factura',
            name='formapago',
            field=models.IntegerField(choices=[(1, 'EFECTIVO'), (3, 'DEPOSITO'), (2, 'TRANSFERENCIA'), (4, 'TARJETA DE CREDITO/DEBITO')], default=1, verbose_name='Forma de pago'),
        ),
    ]
