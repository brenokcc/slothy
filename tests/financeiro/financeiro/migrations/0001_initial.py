# Generated by Django 3.1.7 on 2021-03-09 09:40

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import slothy.db.models.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('api', '0002_user_username'),
    ]

    operations = [
        migrations.CreateModel(
            name='Pessoa',
            fields=[
                ('user_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('nome', slothy.db.models.fields.CharField(max_length=255, verbose_name='Nome')),
                ('email', slothy.db.models.fields.EmailField(max_length=255, unique=True, verbose_name='E-mail')),
                ('foto', models.ImageField(blank=True, null=True, upload_to='fotos', verbose_name='Foto')),
            ],
            options={
                'verbose_name': 'Pessoa',
                'verbose_name_plural': 'Pessoas',
            },
            bases=('api.user',),
        ),
        migrations.CreateModel(
            name='TipoDespesa',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao', slothy.db.models.fields.CharField(max_length=255, verbose_name='Descrição')),
            ],
            options={
                'verbose_name': 'Tipo de Despesa',
                'verbose_name_plural': 'Tipos de Despesa',
            },
        ),
        migrations.CreateModel(
            name='TipoReceita',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao', slothy.db.models.fields.CharField(max_length=255, verbose_name='Descrição')),
            ],
            options={
                'verbose_name': 'Tipo de Receita',
                'verbose_name_plural': 'Tipos de Receita',
            },
        ),
        migrations.CreateModel(
            name='Receita',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao', slothy.db.models.fields.CharField(max_length=255, verbose_name='Descrição')),
                ('data_prevista', models.DateField(verbose_name='Data Prevista')),
                ('valor_previsto', slothy.db.models.fields.DecimalField(decimal_places=2, max_digits=7, verbose_name='Valor Previsto')),
                ('data_recebimento', models.DateField(blank=True, null=True, verbose_name='Data do Recebimento')),
                ('valor_recebido', slothy.db.models.fields.DecimalField(blank=True, decimal_places=2, max_digits=7, null=True, verbose_name='Valor Recebido')),
                ('pessoa', slothy.db.models.fields.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='financeiro.pessoa', verbose_name='Pessoa')),
                ('tipo', slothy.db.models.fields.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='financeiro.tiporeceita', verbose_name='Tipo')),
            ],
            options={
                'verbose_name': 'Receita',
                'verbose_name_plural': 'Receitas',
            },
        ),
        migrations.CreateModel(
            name='Despesa',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao', slothy.db.models.fields.CharField(max_length=255, verbose_name='Descrição')),
                ('data_prevista', models.DateField(verbose_name='Data Prevista')),
                ('valor_previsto', slothy.db.models.fields.DecimalField(decimal_places=2, max_digits=7, verbose_name='Valor Previsto')),
                ('data_pagamento', models.DateField(blank=True, null=True, verbose_name='Data do Pagamento')),
                ('valor_pago', slothy.db.models.fields.DecimalField(blank=True, decimal_places=2, max_digits=7, null=True, verbose_name='Valor Pago')),
                ('pessoa', slothy.db.models.fields.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='financeiro.pessoa', verbose_name='Pessoa')),
                ('tipo', slothy.db.models.fields.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='financeiro.tipodespesa', verbose_name='Tipo')),
            ],
            options={
                'verbose_name': 'Despesa',
                'verbose_name_plural': 'Despesas',
            },
        ),
    ]
