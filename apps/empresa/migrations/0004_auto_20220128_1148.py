# Generated by Django 3.2.8 on 2022-01-28 16:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('empresa', '0003_empresa_descripcioncorta'),
    ]

    operations = [
        migrations.AddField(
            model_name='empresa',
            name='telefono2',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='Telefono 2'),
        ),
        migrations.AddField(
            model_name='empresa',
            name='telefono3',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='Telefono 3'),
        ),
    ]
