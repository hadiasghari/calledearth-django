# Generated by Django 2.2.12 on 2021-05-09 13:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('earth', '0009_auto_20210504_1852'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='prompt',
            name='level',
        ),
        migrations.AddField(
            model_name='prompt',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
    ]
