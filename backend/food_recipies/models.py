from django.contrib.auth import get_user_model
from django.core.validators import (MinValueValidator,
                                    RegexValidator)
from django.db import models

User = get_user_model()


class Ingredients(models.Model):
    name = models.CharField(
            verbose_name='Название',
            max_length=200,
            db_index=True
    )
    measurement_unit = models.CharField(
            verbose_name='Единицы',
            max_length=200
    )

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'
        ordering = ('name',)


class Tags(models.Model):
    name = models.CharField(
            verbose_name='Название',
            max_length=200,
            unique=True
    )
    color = models.CharField(
            verbose_name='Цвет',
            max_length=200,
            unique=True,
            validators=[RegexValidator(r'^#(?:[0-9a-fA-F]{3}){1,2}$')]
    )
    slug = models.SlugField(
            verbose_name='Слаг',
            unique=True
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)


class Recipies(models.Model):
    name = models.CharField(
            verbose_name='Название',
            max_length=200
    )
    author = models.ForeignKey(
            User,
            on_delete=models.CASCADE,
            verbose_name='Автор',
            related_name='recipes',
    )
    image = models.ImageField(
            verbose_name='изображение',
            upload_to='food_recipies/images/',
    )
    text = models.TextField(
            verbose_name='Описание',
            max_length=200
    )
    ingredients = models.ManyToManyField(
            Ingredients,
            verbose_name='Ингредиенты',
            through='IngredientAmount',
    )
    tags = models.ManyToManyField(
            Tags,
            verbose_name='Тег',
    )
    cooking_time = models.PositiveSmallIntegerField(
            verbose_name='Время',
            validators=[MinValueValidator(1)]
    )
    pub_date = models.DateTimeField(
            verbose_name='Дата',
            auto_now_add=True
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)


class ShoppingList(models.Model):
    recipe = models.ForeignKey(
            Recipies,
            verbose_name='Рецепт',
            on_delete=models.CASCADE,
            related_name='carts',
    )
    user = models.ForeignKey(
            User,
            verbose_name='Юзер',
            on_delete=models.CASCADE,
            related_name='carts',
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'


class QuantityOfIngredients(models.Model):
    recipe = models.ForeignKey(
            Recipies,
            on_delete=models.CASCADE,
            related_name='ingredient_in_recipe',
    )
    ingredient = models.ForeignKey(
            Ingredients,
            on_delete=models.CASCADE,
            related_name='recipes_with_ingredient',
    )
    amount = models.IntegerField(
            'Количество',
    )

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'


class Favorites(models.Model):
    recipe = models.ForeignKey(
            Recipies,
            verbose_name='Рецепт',
            on_delete=models.CASCADE,
            related_name='favorites',
    )
    user = models.ForeignKey(
            User,
            verbose_name='Юзер',
            on_delete=models.CASCADE,
            related_name='favorites',
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
