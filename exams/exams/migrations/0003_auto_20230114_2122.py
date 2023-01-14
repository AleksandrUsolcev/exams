# Generated by Django 3.2.16 on 2023-01-14 18:22

import ckeditor_uploader.fields
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('exams', '0002_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Sprint',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Название')),
                ('slug', models.SlugField(editable=False, max_length=340, unique=True, verbose_name='ЧПУ')),
                ('description', ckeditor_uploader.fields.RichTextUploadingField(verbose_name='Описание')),
                ('active', models.BooleanField(default=False, help_text='Статус принимает положительное состояние, если есть хотя бы один не скрытый/готовый к публикации тест', verbose_name='Готов к публикации')),
                ('any_order', models.BooleanField(default=True, verbose_name='Разрешается решать тесты в произвольном порядке')),
            ],
            options={
                'verbose_name': 'Спринт',
                'verbose_name_plural': 'Спринты',
            },
        ),
        migrations.AddField(
            model_name='exam',
            name='priority',
            field=models.PositiveIntegerField(blank=True, help_text='Влияет на порядок выдачи теста, если он относится к спринту', null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(99)], verbose_name='Приоритет'),
        ),
        migrations.AddField(
            model_name='exam',
            name='sprint',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='exams', to='exams.sprint', verbose_name='Спринт'),
        ),
    ]
