# Generated by Django 2.0 on 2021-01-02 07:06

from django.db import migrations, models
import django.db.models.deletion
import slothy.api.models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0003_auto_20201230_1819'),
    ]

    operations = [
        migrations.CreateModel(
            name='Endereco',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('logradouro', models.CharField(max_length=100, verbose_name='Logradouro')),
                ('numero', models.IntegerField(verbose_name='Número')),
            ],
            options={
                'verbose_name': 'Endereço',
                'verbose_name_plural': 'Endereços',
            },
        ),
        migrations.AddField(
            model_name='pessoa',
            name='endereco',
            field=slothy.api.models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='base.Endereco', verbose_name='Endereço'),
        ),
    ]
