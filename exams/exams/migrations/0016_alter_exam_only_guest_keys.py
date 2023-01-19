# Generated by Django 3.2.16 on 2023-01-19 09:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exams', '0015_exam_only_guest_keys'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exam',
            name='only_guest_keys',
            field=models.BooleanField(default=False, help_text='При условии, что пользователю отображается результат', verbose_name='Доступ для гостей к результатам только по ссылке-приглашению'),
        ),
    ]
