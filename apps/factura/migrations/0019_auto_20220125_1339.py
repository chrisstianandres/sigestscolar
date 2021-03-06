# Generated by Django 3.2.8 on 2022-01-25 18:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('factura', '0018_auto_20220125_1325'),
    ]

    operations = [
        migrations.AlterField(
            model_name='factura',
            name='estado',
            field=models.IntegerField(choices=[(2, 'INCORRECTA'), (3, 'ANULADA'), (1, 'CORRECTA')], default=1, verbose_name='Estado Factura'),
        ),
        migrations.AlterField(
            model_name='factura',
            name='formapago',
            field=models.IntegerField(choices=[(2, 'TRANSFERENCIA'), (4, 'TARJETA DE CREDITO/DEBITO'), (3, 'DEPOSITO'), (1, 'EFECTIVO')], default=1, verbose_name='Forma de pago'),
        ),
    ]
