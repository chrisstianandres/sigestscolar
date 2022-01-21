# Generated by Django 3.2.8 on 2022-01-18 01:41

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('producto', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Talla',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.BooleanField(default=True)),
                ('fecha_creacion', models.DateTimeField(blank=True, null=True)),
                ('fecha_modificacion', models.DateTimeField(blank=True, null=True)),
                ('numero', models.IntegerField(default=0)),
                ('talla', models.CharField(blank=True, default='', max_length=4, null=True)),
                ('usuario_creacion', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('usuario_modificacion', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Talla',
                'verbose_name_plural': 'Tallas',
                'ordering': ('numero', 'talla'),
                'unique_together': {('talla', 'numero')},
            },
        ),
        migrations.AddField(
            model_name='producto',
            name='talla',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='producto.talla'),
        ),
    ]
