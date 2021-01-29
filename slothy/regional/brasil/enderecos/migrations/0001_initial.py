# Generated by Django 3.1.5 on 2021-01-28 17:13

from django.db import migrations, models
import django.db.models.deletion
import slothy.db.models.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Estado',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', slothy.db.models.fields.CharField(max_length=255, verbose_name='Nome')),
                ('sigla', slothy.db.models.fields.CharField(max_length=255, verbose_name='Sigla')),
                ('codigo', slothy.db.models.fields.CharField(max_length=255, verbose_name='Código')),
                ('geo', models.TextField(blank=True, null=True, verbose_name='Geolocalização')),
            ],
            options={
                'verbose_name': 'Estado',
                'verbose_name_plural': 'Estados',
            },
        ),
        migrations.CreateModel(
            name='Regiao',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', slothy.db.models.fields.CharField(max_length=255, verbose_name='Nome')),
                ('codigo', slothy.db.models.fields.CharField(max_length=255, verbose_name='Código')),
                ('geo', models.TextField(blank=True, null=True, verbose_name='Geolocalização')),
            ],
            options={
                'verbose_name': 'Região',
                'verbose_name_plural': 'Regiões',
            },
        ),
        migrations.CreateModel(
            name='Municipio',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', slothy.db.models.fields.CharField(max_length=255, verbose_name='Nome')),
                ('codigo', slothy.db.models.fields.CharField(max_length=255, verbose_name='Código')),
                ('geo', models.TextField(blank=True, null=True, verbose_name='Geolocalização')),
                ('estado', slothy.db.models.fields.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='enderecos.estado', verbose_name='Estado')),
            ],
            options={
                'verbose_name': 'Município',
                'verbose_name_plural': 'Municípios',
            },
        ),
        migrations.AddField(
            model_name='estado',
            name='regiao',
            field=slothy.db.models.fields.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='enderecos.regiao', verbose_name='Região'),
        ),
        migrations.CreateModel(
            name='Endereco',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cep', slothy.db.models.fields.MaskedField(max_length=255, verbose_name='CEP')),
                ('logradouro', slothy.db.models.fields.CharField(max_length=255, verbose_name='Logradouro')),
                ('numero', slothy.db.models.fields.CharField(max_length=255, verbose_name='Número')),
                ('complemento', slothy.db.models.fields.CharField(blank=True, max_length=255, null=True, verbose_name='Complemento')),
                ('bairro', slothy.db.models.fields.CharField(max_length=255, verbose_name='Bairro')),
                ('municipio', slothy.db.models.fields.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='enderecos.municipio', verbose_name='Município')),
            ],
            options={
                'verbose_name': 'Endereço',
                'verbose_name_plural': 'Endereços',
            },
        ),
    ]