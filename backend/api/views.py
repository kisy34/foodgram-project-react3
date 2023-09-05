from core.filters import RecipeFilter
from core.pagination import CustomPagination
from core.pdf_download import getpdf
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, views, viewsets
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.validators import ValidationError

from ..food_recipies.models import (Favorites, Ingredients,
                                    QuantityOfIngredients, Recipies,
                                    ShoppingList, Tags)
from ..users.models import Follower
from .permissions import IsAdminOrReadOnly, IsOwnerOrReadOnly
from .serializers import (CustomUsersSerializer, FollowersSerializer,
                          FollowsSerializer, IngredientsSerializer,
                          NewRecipesSerializer, PasswordSerializer,
                          RecipeSerializer, TagsSerializer,
                          UsersPostsSerializer)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return CustomUsersSerializer
        return UsersPostsSerializer

    @action(
        detail=False, methods=['GET'], permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        user = get_object_or_404(User, pk=request.user.id)
        serializer = CustomUsersSerializer(user)
        return Response(serializer.data)

    @action(detail=False, methods=['POST'])
    def set_password(self, request):
        user = self.request.user
        serializer = PasswordSerializer(data=request.data)
        if serializer.is_valid():
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'result': 'Done!'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FollowView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = FollowsSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        return user.follower.all()


class FollowToView(views.APIView):
    pagination_class = CustomPagination
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk):
        author = get_object_or_404(User, pk=pk)
        user = self.request.user
        data = {'author': author.id, 'user': user.id}
        serializer = FollowersSerializer(
            data=data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, pk):
        author = get_object_or_404(User, pk=pk)
        user = self.request.user
        following = get_object_or_404(
            Follower, user=user, author=author
        )
        following.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tags.objects.all()
    serializer_class = TagsSerializer
    permission_classes = (IsAdminOrReadOnly,)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    class CustomSearchFilter(filters.SearchFilter):
        search_param = 'name'

    queryset = Ingredients.objects.all()
    search_fields = ('^name',)
    serializer_class = IngredientsSerializer
    filter_backends = [CustomSearchFilter]


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipies.objects.all()
    permission_classes = (IsOwnerOrReadOnly,)
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeSerializer
        return NewRecipesSerializer

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(author=user)

    @action(
        detail=True,
        methods=('POST', 'DELETE'),
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk=None):
        if request.method == 'POST':
            return self.add_recipe(Favorites, request, pk)
        return self.delete_recipe(Favorites, request, pk)

    @action(
        detail=True,
        methods=('POST', 'DELETE'),
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):
        if request.method == 'POST':
            return self.add_recipe(ShoppingList, request, pk)
        return self.delete_recipe(ShoppingList, request, pk)

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        ingredients = QuantityOfIngredients.objects.filter(
            recipe__carts__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).order_by(
            'ingredient__name'
        ).annotate(ingredient_amount=Sum('amount'))
        return getpdf(ingredients)

    def add_recipe(self, model, pk):
        recipie = get_object_or_404(Recipies, pk=pk)
        user = self.request.user
        if model.objects.filter(recipe=recipie, user=user).exists():
            raise ValidationError('Error')
        model.objects.create(recipe=recipie, user=user)
        serializer = RecipeSerializer(recipie)
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    def delete_recipe(self, model, pk):
        recipe = get_object_or_404(Recipies, pk=pk)
        user = self.request.user
        obj = get_object_or_404(model, recipe=recipe, user=user)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
