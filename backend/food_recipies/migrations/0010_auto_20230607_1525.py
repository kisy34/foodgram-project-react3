# Generated by Django 3.2.3 on 2023-06-07 15:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('food_recipies', '0009_alter_ingredientamount_ingredient'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='cart',
            options={'verbose_name': 'Рецепт в списке покупок', 'verbose_name_plural': 'Рецепты в списке покупок'},
        ),
        migrations.AlterModelOptions(
            name='favorite',
            options={'verbose_name': 'Рецепт в списке избранного', 'verbose_name_plural': 'Рецепты в списке избранного'},
        ),
    ]
