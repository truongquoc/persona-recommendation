# Generated by Django 4.2.14 on 2024-07-27 00:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restaurants', '0002_restaurant_adventure_rating_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='restaurant',
            name='main_image_url',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='restaurant',
            name='price_level',
            field=models.IntegerField(choices=[(1, '$'), (2, '$$'), (3, '$$$'), (4, '$$$$'), (5, '$$$$$')], null=True),
        ),
        migrations.AlterField(
            model_name='userpreference',
            name='preferred_price_level',
            field=models.IntegerField(choices=[(1, '$'), (2, '$$'), (3, '$$$'), (4, '$$$$'), (5, '$$$$$')], null=True),
        ),
    ]
