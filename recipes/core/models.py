import uuid

from django.contrib.auth import get_user_model
from django.db.models import (
    Model,
    DateTimeField,
    UUIDField,
    CharField,
    PositiveIntegerField,
    ForeignKey,
    PROTECT,
    FloatField,
    TextField,
    ManyToManyField,
)

User = get_user_model()


class BaseModel(Model):
    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = DateTimeField(auto_now_add=True, db_index=True)
    updated_at = DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True


class Recipe(BaseModel):
    name = CharField(max_length=255, null=False, blank=False, db_index=True)
    serves = PositiveIntegerField(null=False, blank=False, db_index=True)
    preparation_time_in_minutes = PositiveIntegerField(
        null=False, blank=False, db_index=True
    )
    preparation = TextField(null=False, blank=False)
    ingredients = ManyToManyField("core.RecipeIngredient")
    author = ForeignKey(User, null=False, blank=False, on_delete=PROTECT)

    class Meta:
        verbose_name = "Recipe"
        verbose_name_plural = "Recipes"
        ordering = ("name", "-created_at")


class Ingredient(BaseModel):
    name = CharField(
        max_length=255, null=False, blank=False, db_index=True, unique=True
    )

    class Meta:
        verbose_name = "Ingredient"
        verbose_name_plural = "Ingredients"
        ordering = ("name", "-created_at")


class Unit(BaseModel):
    name = CharField(
        max_length=255, null=False, blank=False, db_index=True, unique=True
    )
    abbreviation = CharField(
        max_length=10, null=False, blank=False, db_index=True, unique=True
    )

    class Meta:
        verbose_name = "Unit"
        verbose_name_plural = "Units"
        ordering = ("name", "-created_at")


class RecipeIngredient(BaseModel):
    ingredient = ForeignKey(
        "core.Ingredient", null=False, blank=False, on_delete=PROTECT
    )
    quantity = FloatField(null=False, blank=False)
    unit = ForeignKey("core.Unit", null=False, blank=False, on_delete=PROTECT)

    class Meta:
        verbose_name = "Recipe Ingredient"
        verbose_name_plural = "Recipes Ingredients"
        ordering = ("recipe__name", "ingredient__name", "-created_at")
