# Generated by Django 4.2.14 on 2024-07-28 01:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restaurants', '0004_restaurant_opening_hours_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='restaurant',
            name='vegan_options',
            field=models.BooleanField(default=False),
        ),
    ]