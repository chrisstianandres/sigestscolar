# Generated by Django 3.2.8 on 2022-01-28 15:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('factura', '0021_auto_20220126_1959'),
    ]

    operations = [
        migrations.AlterField(
            model_name='factura',
            name='estado',
            field=models.IntegerField(choices=[(1, 'CORRECTA'), (3, 'ANULADA'), (2, 'INCORRECTA')], default=1, verbose_name='Estado Factura'),
        ),
        migrations.AlterField(
            model_name='factura',
            name='formapago',
            field=models.IntegerField(choices=[(1, 'EFECTIVO'), (4, 'TARJETA DE CREDITO/DEBITO'), (2, 'TRANSFERENCIA'), (3, 'DEPOSITO')], default=1, verbose_name='Forma de pago'),
        ),
    ]
