# Generated by Django 3.2.8 on 2022-01-22 20:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('factura', '0011_auto_20220122_1342'),
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
            field=models.IntegerField(choices=[(2, 'TRANSFERENCIA'), (3, 'DEPOSITO'), (4, 'TARJETA DE CREDITO/DEBITO'), (1, 'EFECTIVO')], default=1, verbose_name='Forma de pago'),
        ),
    ]
