from rest_framework.viewsets import ModelViewSet

from core.views import CustomPageNumberPagination
from social.models import Like
from social.serializers import LikeSerializer


class LikeViewSet(ModelViewSet):
    queryset = Like.objects.all()
    serializer_class = LikeSerializer
    filterset_fields = ("id", "recipe", "comment", "user")
    pagination_class = CustomPageNumberPagination


class CommentViewSet(ModelViewSet):
    queryset = Like.objects.all()
    serializer_class = LikeSerializer
    filterset_fields = ("id", "recipe", "user")
    pagination_class = CustomPageNumberPagination
