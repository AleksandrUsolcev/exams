# Generated by Django 3.2.16 on 2023-01-11 11:32

import ckeditor.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('exams', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='description',
            field=ckeditor.fields.RichTextField(blank=True, null=True, verbose_name='Подробное описание/информация'),
        ),
    ]