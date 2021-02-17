# Generated by Django 3.1.5 on 2021-02-17 19:32

from django.db import migrations
import slothy.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0004_pontoturistico_ativo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cidade',
            name='localizacao',
            field=slothy.db.models.fields.GeoLocationField(blank=True, max_length=255, null=True, verbose_name='Localização'),
        ),
        migrations.AlterField(
            model_name='pessoa',
            name='email',
            field=slothy.db.models.fields.EmailField(max_length=255, unique=True, verbose_name='E-mail'),
        ),
    ]
