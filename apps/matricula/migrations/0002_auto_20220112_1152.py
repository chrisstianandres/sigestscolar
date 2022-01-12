# Generated by Django 3.2.8 on 2022-01-12 16:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('matricula', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='matricula',
            name='pensiones',
        ),
        migrations.AddField(
            model_name='pension',
            name='matricula',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='matricula.matricula', verbose_name='Matricula'),
        ),
    ]