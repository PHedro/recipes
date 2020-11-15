from rest_framework.serializers import ModelSerializer

from social.models import Like, Comment


class LikeSerializer(ModelSerializer):
    class Meta:
        model = Like
        fields = (
            "id",
            "user",
            "recipe",
            "comment",
            "created_at",
        )


class CommentSerializer(ModelSerializer):
    class Meta:
        model = Comment
        fields = (
            "id",
            "user",
            "recipe",
            "in_reply_to",
            "content",
            "created_at",
            "updated_at",
        )
