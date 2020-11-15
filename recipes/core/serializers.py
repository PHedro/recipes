from django.contrib.auth import get_user_model
from drf_writable_nested import (
    UniqueFieldsMixin,
    WritableNestedModelSerializer,
)
from rest_framework.serializers import ModelSerializer

from core.models import Unit, Ingredient, RecipeIngredient, Recipe


class UnitSerializer(UniqueFieldsMixin, ModelSerializer):
    class Meta:
        model = Unit
        fields = ("id", "name", "abbreviation")


class IngredientSerializer(UniqueFieldsMixin, ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name")


class RecipeIngredientSerializer(WritableNestedModelSerializer):
    ingredient = IngredientSerializer(many=False, required=True)
    unit = UnitSerializer(many=False, required=True)

    class Meta:
        model = RecipeIngredient
        fields = ("id", "ingredient", "quantity", "unit")


class UserSerializer(UniqueFieldsMixin, ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = (
            "id",
            "username",
            "email",
        )


class RecipeSerializer(WritableNestedModelSerializer):
    ingredients = RecipeIngredientSerializer(many=True)
    author = UserSerializer(many=False, required=True)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "name",
            "serves",
            "preparation_time_in_minutes",
            "preparation",
            "ingredients",
            "author",
        )
