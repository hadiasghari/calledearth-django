# Generated by Django 2.2.12 on 2021-05-13 23:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('earth', '0013_auto_20210514_0048'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eventqueue',
            name='game',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='earth.GamePlay'),
        ),
        migrations.AlterField(
            model_name='eventqueue',
            name='participant',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='earth.Participant'),
        ),
    ]
