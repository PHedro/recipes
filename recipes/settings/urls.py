from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from core.views import IngredientViewSet, RecipeViewSet, UnitViewSet

router = DefaultRouter()
router.register(r"ingredients", IngredientViewSet)
router.register(r"recipes", RecipeViewSet)
router.register(r"units", UnitViewSet)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
]
