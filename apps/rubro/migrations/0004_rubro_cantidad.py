# Generated by Django 3.2.8 on 2022-01-16 18:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rubro', '0003_alter_rubro_pension'),
    ]

    operations = [
        migrations.AddField(
            model_name='rubro',
            name='cantidad',
            field=models.IntegerField(default=1, verbose_name='Producto'),
        ),
    ]
