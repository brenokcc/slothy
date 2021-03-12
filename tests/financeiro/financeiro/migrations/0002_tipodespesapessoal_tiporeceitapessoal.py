# Generated by Django 3.1.7 on 2021-03-12 09:52

from django.db import migrations, models
import django.db.models.deletion
import slothy.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('financeiro', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TipoReceitaPessoal',
            fields=[
                ('tiporeceita_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='financeiro.tiporeceita')),
                ('pessoa', slothy.db.models.fields.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='financeiro.pessoa', verbose_name='Pessoa')),
            ],
            options={
                'verbose_name': 'Tipo de Despesa',
                'verbose_name_plural': 'Tipos de Despesa',
            },
            bases=('financeiro.tiporeceita',),
        ),
        migrations.CreateModel(
            name='TipoDespesaPessoal',
            fields=[
                ('tipodespesa_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='financeiro.tipodespesa')),
                ('pessoa', slothy.db.models.fields.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='financeiro.pessoa', verbose_name='Pessoa')),
            ],
            options={
                'verbose_name': 'Tipo de Despesa',
                'verbose_name_plural': 'Tipos de Despesa',
            },
            bases=('financeiro.tipodespesa',),
        ),
    ]
