# Generated by Django 2.0 on 2020-12-24 02:14

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import slothy.api.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Pessoa',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(blank=True, default='!', max_length=255, null=True, verbose_name='Senha')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='Último Login')),
                ('email', models.EmailField(max_length=255, unique=True, verbose_name='E-mail')),
                ('nome', models.CharField(max_length=255, verbose_name='Nome')),
                ('foto', models.ImageField(blank=True, null=True, upload_to='fotos', verbose_name='Foto')),
            ],
            options={
                'verbose_name': 'Pessoa',
                'verbose_name_plural': 'Pessoas',
            },
        ),
        migrations.CreateModel(
            name='Cidade',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=255, verbose_name='Nome')),
            ],
            options={
                'verbose_name': 'Estado',
                'verbose_name_plural': 'Estados',
            },
        ),
        migrations.CreateModel(
            name='Estado',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=255, verbose_name='Nome')),
                ('sigla', models.CharField(max_length=255, verbose_name='Sigla')),
                ('ativo', models.BooleanField(default=True, verbose_name='Ativo')),
            ],
            options={
                'verbose_name': 'Estado',
                'verbose_name_plural': 'Estados',
            },
        ),
        migrations.CreateModel(
            name='Governador',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estado', slothy.api.models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.Estado', verbose_name='Estado')),
            ],
            options={
                'verbose_name': 'Governador',
                'verbose_name_plural': 'Governadores',
            },
        ),
        migrations.CreateModel(
            name='PontoTuristico',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=255, verbose_name='Nome')),
            ],
            options={
                'verbose_name': 'Ponto Turístico',
                'verbose_name_plural': 'Pontos Turísticos',
            },
        ),
        migrations.CreateModel(
            name='Presidente',
            fields=[
                ('pessoa_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Presidente',
                'verbose_name_plural': 'Presidentes',
            },
            bases=('base.pessoa',),
        ),
        migrations.AddField(
            model_name='governador',
            name='usuario',
            field=slothy.api.models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Usuário'),
        ),
        migrations.AddField(
            model_name='cidade',
            name='estado',
            field=slothy.api.models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.Estado', verbose_name='Estado'),
        ),
        migrations.AddField(
            model_name='cidade',
            name='pontos_turisticos',
            field=models.ManyToManyField(to='base.PontoTuristico', verbose_name='Pontos Turísticos'),
        ),
        migrations.AddField(
            model_name='cidade',
            name='prefeito',
            field=slothy.api.models.RoleForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Prefeito'),
        ),
        migrations.AddField(
            model_name='cidade',
            name='vereadores',
            field=slothy.api.models.RoleManyToManyField(blank=True, related_name='cidades_legisladas', to=settings.AUTH_USER_MODEL, verbose_name='Vereadores'),
        ),
        migrations.AddField(
            model_name='pessoa',
            name='groups',
            field=models.ManyToManyField(blank=True, to='api.Group', verbose_name='Grupos'),
        ),
    ]
