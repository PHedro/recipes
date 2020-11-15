from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import ModelViewSet

from core.models import Ingredient, Recipe, Unit
from core.serializers import (
    IngredientSerializer,
    RecipeSerializer,
    UnitSerializer,
)


class CustomPageNumberPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 100
    page_size_query_param = "page_size"


class UnitViewSet(ModelViewSet):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer
    filterset_fields = ("id", "name")
    pagination_class = CustomPageNumberPagination


class IngredientViewSet(ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filterset_fields = ("id", "name")
    pagination_class = CustomPageNumberPagination


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    filterset_fields = (
        "id",
        "name",
        "serves",
        "preparation_time_in_minutes",
        "author",
    )
    pagination_class = CustomPageNumberPagination
