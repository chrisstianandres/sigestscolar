# Generated by Django 3.2.8 on 2022-01-28 16:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('factura', '0024_auto_20220128_1137'),
    ]

    operations = [
        migrations.AlterField(
            model_name='factura',
            name='estado',
            field=models.IntegerField(choices=[(1, 'CORRECTA'), (2, 'INCORRECTA'), (3, 'ANULADA')], default=1, verbose_name='Estado Factura'),
        ),
        migrations.AlterField(
            model_name='factura',
            name='formapago',
            field=models.IntegerField(choices=[(3, 'DEPOSITO'), (2, 'TRANSFERENCIA'), (1, 'EFECTIVO'), (4, 'TARJETA DE CREDITO/DEBITO')], default=1, verbose_name='Forma de pago'),
        ),
    ]
