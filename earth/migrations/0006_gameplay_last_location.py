# Generated by Django 2.2.12 on 2021-05-02 16:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('earth', '0005_auto_20210502_1124'),
    ]

    operations = [
        migrations.AddField(
            model_name='gameplay',
            name='last_location',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
