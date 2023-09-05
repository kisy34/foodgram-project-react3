from django.contrib.auth import get_user_model
from django.db import transaction
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from ..food_recipies.models import (Favorites, Ingredients,
                                    QuantityOfIngredients, Recipies,
                                    ShoppingList, Tags)
from ..users.models import Follower

User = get_user_model()


class UsersPostsSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = ['email', 'id', 'username', 'first_name', 'last_name',
                  'password']


class CustomUsersSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField(
        method_name='get_is_subscribed')

    class Meta:
        model = User
        fields = ['email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed']

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Follower.objects.filter(user=request.user, author=obj).exists()


class FollowsSerializer(serializers.ModelSerializer):
    email = serializers.ReadOnlyField(source='author.email')
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField(
        method_name='get_is_subscribed')
    recipes = serializers.SerializerMethodField(method_name='get_recipes')
    recipes_count = serializers.SerializerMethodField(
        method_name='get_recipes_count')

    class Meta:
        model = Follower
        fields = ['email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count']

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return Follower.objects.filter(author=obj.author,
                                       user=request.user).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        if request.GET.get('recipe_limit'):
            lim = int(request.GET.get('recipe_limit'))
            queryset = Recipies.objects.filter(author=obj.author)[
                :lim]
        else:
            queryset = Recipies.objects.filter(author=obj.author)
        serializer = RecipeSerializer(queryset, read_only=True, many=True)
        return serializer.data

    def get_recipes_count(self, obj):
        return obj.author.recipes.count()


class RecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipies
        fields = ['id', 'name', 'image', 'cooking_time']


class FollowersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follower
        fields = ['user', 'author']

    def validate(self, data):
        user = data.get('user')
        author = data.get('author')
        if user == author:
            raise serializers.ValidationError('Dont follow yourself')
        if Follower.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError('Error')
        return data

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        serializer = FollowsSerializer(instance, context=context)
        return serializer.data


class TagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = ['id', 'name', 'color', 'slug']
        read_only_fields = ['id', 'name', 'color', 'slug']


class IngredientsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredients
        fields = ['id', 'name', 'measurement_unit']
        read_only_fields = ['id', 'name', 'measurement_unit']


class NewIngredientsSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredients.objects.all(),
                                            source='ingredient')
    amount = serializers.IntegerField()

    class Meta:
        model = QuantityOfIngredients
        fields = ['id', 'amount']


class NewRecipesSerializer(serializers.ModelSerializer):
    image = Base64ImageField(max_length=None, use_url=True)
    author = CustomUsersSerializer(read_only=True)
    ingredients = NewIngredientsSerializer(many=True,
                                           source='ingredient_in_recipe')
    tags = serializers.PrimaryKeyRelatedField(queryset=Tags.objects.all(),
                                              many=True)

    class Meta:
        model = Recipies
        fields = ['id', 'tags', 'author', 'ingredients', 'name', 'image',
                  'text', 'cooking_time']

    def bulk_create_ingredients(self, ingredients, recipe):
        ingredients1 = list()
        ingredients2 = set()
        for ingredient in ingredients:
            amount1 = ingredient['amount']
            ingredient1 = ingredient['ingredient']
            if ingredient1 in ingredients2:
                raise serializers.ValidationError({'denied': 'no dublicates'})
            else:
                ingredients2.add(ingredient1)
            ingredients1.append(
                QuantityOfIngredients(recipe=recipe,
                                      ingredient=ingredient1,
                                      amount=amount1))
        QuantityOfIngredients.objects.bulk_create(ingredients1)

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredient_in_recipe')
        tags = validated_data.pop('tags')
        recipies = Recipies.objects.create(**validated_data)
        self.bulk_create_ingredients(ingredients, recipies)
        recipies.tags.set(tags)
        recipies.save()
        return recipies

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredient_in_recipe')
        tags = validated_data.pop('tags')
        QuantityOfIngredients.objects.filter(recipe=instance).delete()
        self.bulk_create_ingredients(ingredients, instance)
        instance.name = validated_data.pop('name')
        instance.text = validated_data.pop('text')
        if validated_data.get('image') is not None:
            instance.image = validated_data.pop('image')
        instance.cooking_time = validated_data.pop('cooking_time')
        instance.tags.set(tags)
        instance.save()
        return instance


class IngredientsQuantitySerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = QuantityOfIngredients
        fields = ['id', 'name', 'measurement_unit', 'amount']


class RecipesSerializer(serializers.ModelSerializer):
    author = CustomUsersSerializer()
    tags = TagsSerializer(many=True, )
    ingredients = IngredientsQuantitySerializer(source='ingredient_in_recipe',
                                                read_only=True, many=True)
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField(
        method_name='get_is_favorited')
    is_in_shopping_cart = serializers.SerializerMethodField(
        method_name='get_is_in_shopping_cart')

    class Meta:
        model = Recipies
        fields = ['id', 'tags', 'name', 'author', 'ingredients', 'image',
                  'text', 'cooking_time', 'is_favorited', 'is_in_shopping_cart'
                  ]

    def is_exists_in(self, obj, model):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return model.objects.filter(user=request.user, recipe=obj).exists()

    def get_is_favorited(self, obj):
        return self.is_exists_in(obj, Favorites)

    def get_is_in_shopping_cart(self, obj):
        return self.is_exists_in(obj, ShoppingList)


class PasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True)
    current_password = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ['email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed']
