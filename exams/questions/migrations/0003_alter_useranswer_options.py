# Generated by Django 3.2.16 on 2022-12-31 08:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('questions', '0002_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='useranswer',
            options={'ordering': ['date'], 'verbose_name': 'Ответ пользователя', 'verbose_name_plural': 'Ответы пользователей'},
        ),
    ]