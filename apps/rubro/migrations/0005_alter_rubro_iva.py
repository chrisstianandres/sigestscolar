# Generated by Django 3.2.8 on 2022-01-22 20:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('empresa', '0001_initial'),
        ('rubro', '0004_rubro_cantidad'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rubro',
            name='iva',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='empresa.empresa', verbose_name='IVA'),
        ),
    ]