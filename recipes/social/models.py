from django.contrib.auth import get_user_model
from django.db.models import ForeignKey, PROTECT, TextField

from core.models import BaseModel

User = get_user_model()


class UserRecipeModelMixin(BaseModel):
    user = ForeignKey(
        User, null=False, blank=False, on_delete=PROTECT, editable=False
    )
    recipe = ForeignKey(
        "core.Recipe",
        null=False,
        blank=False,
        on_delete=PROTECT,
        editable=False,
    )

    class Meta:
        abstract = True


class Comment(UserRecipeModelMixin):
    in_reply_to = ForeignKey(
        "self", null=True, blank=False, on_delete=PROTECT, editable=False
    )
    content = TextField(null=False, blank=False)

    class Meta:
        verbose_name = "Comment"
        verbose_name_plural = "Comments"
        ordering = ("-created_at", "user__username")


class Like(UserRecipeModelMixin):
    # in future versions change for generic foreign Key
    # instead of using two columns
    comment = ForeignKey(
        "social.Comment",
        null=True,
        blank=False,
        on_delete=PROTECT,
        editable=False,
    )

    class Meta:
        verbose_name = "Like"
        verbose_name_plural = "Likes"
        ordering = ("-created_at", "user__username")
