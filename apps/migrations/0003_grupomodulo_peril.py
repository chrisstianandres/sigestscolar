# Generated by Django 3.2.8 on 2022-01-10 17:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('perfil', '0001_initial'),
        ('apps', '0002_grupomodulo'),
    ]

    operations = [
        migrations.AddField(
            model_name='grupomodulo',
            name='peril',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='perfil.perfilusuario'),
        ),
    ]
