# Generated by Django 2.2.12 on 2021-05-17 12:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('earth', '0016_auto_20210514_1232'),
    ]

    operations = [
        migrations.RenameField(
            model_name='prompt',
            old_name='description',
            new_name='comments',
        ),
        migrations.AddField(
            model_name='gameplay',
            name='state',
            field=models.CharField(blank=True, default='', max_length=10),
        ),
        migrations.AlterField(
            model_name='gamelog',
            name='game',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='earth.GamePlay'),
        ),
        migrations.AlterField(
            model_name='participant',
            name='game',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='earth.GamePlay'),
        ),
    ]
