# Generated by Django 2.2.12 on 2021-05-02 09:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('earth', '0002_auto_20210425_2023'),
    ]

    operations = [
        migrations.RenameField(
            model_name='gameplay',
            old_name='notes',
            new_name='description',
        ),
        migrations.AddField(
            model_name='participant',
            name='location',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
