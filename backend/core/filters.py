from django.contrib.auth import get_user_model
from django_filters.rest_framework import FilterSet, filters
from food_recipies.models import Recipies, Tags

User = get_user_model()


class RecipeFilter(FilterSet):
    author = filters.ModelChoiceFilter(queryset=User.objects.all())
    tags = filters.ModelMultipleChoiceFilter(
            field_name='tags__slug',
            queryset=Tags.objects.all(),
            to_field_name='slug',
    )
    is_favorited = filters.BooleanFilter(method='get_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
            method='get_is_in_shopping_cart'
    )

    class Meta:
        model = Recipies
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    def get_is_favorited(self, queryset, value):
        if value:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, value):
        if value:
            return queryset.filter(carts__user=self.request.user)
        return queryset
