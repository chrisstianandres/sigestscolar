# Generated by Django 3.2.8 on 2022-01-10 22:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('factura', '0003_alter_factura_estado'),
    ]

    operations = [
        migrations.AlterField(
            model_name='factura',
            name='estado',
            field=models.IntegerField(choices=[(1, 'CORRECTA'), (3, 'ANULADA'), (2, 'INCORRECTA')], default=1, verbose_name='Estado Factura'),
        ),
    ]
