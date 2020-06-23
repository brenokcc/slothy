# Generated by Django 3.0.7 on 2020-06-22 18:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0003_cidade_estado'),
    ]

    operations = [
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
        migrations.AddField(
            model_name='cidade',
            name='pontos_turisticos',
            field=models.ManyToManyField(to='base.PontoTuristico', verbose_name='Pontos Turísticos'),
        ),
    ]