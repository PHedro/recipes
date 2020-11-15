import re
from uuid import UUID

from django.contrib.auth import get_user_model
from django.test import TestCase
from model_bakery import baker

from core.tests import BaseSerializerTestCaseMixin, UUID_PATTERN
from social.models import Like, Comment
from social.serializers import LikeSerializer, CommentSerializer


class LikeSerializerTestCase(TestCase, BaseSerializerTestCaseMixin):
    required_data = {}
    unique_fields = {}
    model_str = "social.Like"
    serializer_class = LikeSerializer
    model = Like

    def setUp(self):
        self.recipe = baker.make("core.Recipe")
        self.comment = baker.make("social.Comment")
        self.user, _ = get_user_model().objects.get_or_create(
            email="foo@bar.com", username="foobar"
        )

    def get_full_data(self):
        return {
            "recipe": self.recipe.id,
            "comment": self.comment.id,
            "user": self.user.id,
        }

    def get_default_data(self):
        return {
            "recipe": self.recipe,
            "comment": self.comment,
            "user": self.user,
        }

    def get_update_data(self):
        return {
            "recipe": self.recipe.id,
            "comment": self.comment.id,
            "user": self.user.id,
        }

    def dict_structure_is_valid(self, data):
        result = True
        try:
            result = (
                result
                and isinstance(data["id"], str)
                and re.match(pattern=UUID_PATTERN, string=data["id"])
            )
            result = result and isinstance(data["user"], int)
            if data.get("recipe"):
                result = (
                    result
                    and isinstance(data["recipe"], (str, UUID))
                    and re.match(
                        pattern=UUID_PATTERN, string=str(data["recipe"])
                    )
                )
            if data.get("comment"):
                result = (
                    result
                    and isinstance(data["comment"], (str, UUID))
                    and re.match(
                        pattern=UUID_PATTERN, string=str(data["comment"])
                    )
                )
        except:
            result = False

        return result


class CommentSerializerTestCase(TestCase, BaseSerializerTestCaseMixin):
    required_data = {}
    unique_fields = {}
    model_str = "social.Comment"
    serializer_class = CommentSerializer
    model = Comment

    def setUp(self):
        self.recipe = baker.make("core.Recipe")
        self.comment = baker.make("social.Comment")
        self.user, _ = get_user_model().objects.get_or_create(
            email="foo@bar.com", username="foobar"
        )

    def get_full_data(self):
        return {
            "recipe": self.recipe.id,
            "in_reply_to": self.comment.id,
            "user": self.user.id,
            "content": "comments here",
        }

    def get_update_data(self):
        return {
            "recipe": self.recipe.id,
            "in_reply_to": self.comment.id,
            "user": self.user.id,
            "content": "comment here  edited",
        }

    def get_default_data(self):
        return {
            "recipe": self.recipe,
            "in_reply_to": self.comment,
            "user": self.user,
            "content": "comment here",
        }

    def dict_structure_is_valid(self, data):
        result = True
        try:
            result = (
                result
                and isinstance(data["id"], str)
                and re.match(pattern=UUID_PATTERN, string=data["id"])
            )
            result = result and isinstance(data["user"], int)
            result = result and isinstance(data["content"], str)
            if data.get("recipe"):
                result = (
                    result
                    and isinstance(data["recipe"], (str, UUID))
                    and re.match(
                        pattern=UUID_PATTERN, string=str(data["recipe"])
                    )
                )
            if data.get("in_reply_to"):
                result = (
                    result
                    and isinstance(data["in_reply_to"], (str, UUID))
                    and re.match(
                        pattern=UUID_PATTERN, string=str(data["in_reply_to"])
                    )
                )
        except:
            result = False

        return result
