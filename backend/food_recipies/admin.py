from django.contrib import admin

from .models import (Favorites, Ingredients, QuantityOfIngredients, Recipies,
                     ShoppingList, Tags)


class IngredientsInLine(admin.TabularInline):
    model = Recipies.ingredients.through


class TagsInLine(admin.TabularInline):
    model = Recipies.tags.through


@admin.register(Tags)
class TagAdmin(admin.ModelAdmin):
    fields = ['name', 'color', 'slug']


@admin.register(Ingredients)
class IngredientAdmin(admin.ModelAdmin):
    list_filter = ['name']
    list_display = ['name', 'measurement_unit']


@admin.register(Recipies)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ['name', 'author', 'count_favorite']
    list_filter = ['name', 'author', 'tags']
    inlines = (IngredientsInLine, TagsInLine)

    def count_favorite(self, instance):
        return instance.favorites.count()


@admin.register(QuantityOfIngredients)
class IngredientAmount(admin.ModelAdmin):
    list_display = ['ingredient', 'recipe', 'amount']


@admin.register(Favorites)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['recipe', 'user']


@admin.register(ShoppingList)
class CartAdmin(admin.ModelAdmin):
    list_display = ['recipe', 'user']
