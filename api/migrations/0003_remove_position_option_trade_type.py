# Generated by Django 3.2.9 on 2021-12-08 07:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_auto_20211208_0746'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='position_option',
            name='trade_type',
        ),
    ]