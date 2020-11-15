import json
import re
from copy import copy
from unittest.case import skip

from django.contrib.auth import get_user_model
from django.test import TestCase
from model_bakery import baker
from rest_framework.exceptions import ValidationError
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
)
from rest_framework.test import APIClient

from core.models import Unit, Ingredient, RecipeIngredient, Recipe
from core.serializers import (
    UnitSerializer,
    IngredientSerializer,
    RecipeIngredientSerializer,
    RecipeSerializer,
)

UUID_PATTERN = r"(?P<uuid>[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12})"


class BaseSerializerTestCaseMixin:
    def create_instance(self):
        return baker.make(
            getattr(self, "model_str"), **self.get_default_data()
        )

    def get_full_data(self):
        return getattr(self, "full_data")

    def get_default_data(self):
        return getattr(self, "default_data")

    def get_update_data(self):
        return getattr(self, "update_data")

    def get_serializer_class(self):
        return getattr(self, "serializer_class")

    def create_instance_to_be_duplicated_on_post(self):
        return self.create_instance()

    def dict_structure_is_valid(self, data):
        raise NotImplementedError

    def get_queryset(self):
        qset = getattr(self, "queryset", None)
        if not qset:
            qset = getattr(self, "model").objects.all()
        return qset

    def tearDown(self):
        for model in getattr(self, "models_to_clean", []):
            model.objects.all().delete()

    def test_is_valid_with_all_data(self):
        serializer = self.get_serializer_class()(
            data=self.get_full_data(), many=False
        )
        result = serializer.is_valid(raise_exception=False)
        self.assertTrue(result)

    def test_is_invalid_without_required_data(self):
        _required = getattr(self, "required_data")
        if _required:
            _data = {
                key: value
                for key, value in self.get_full_data().items()
                if key not in _required
            }
            serializer = self.get_serializer_class()(data=_data, many=False)
            result = serializer.is_valid(raise_exception=False)
            self.assertFalse(result)
        else:
            skip("Not applicable, model does not have any required field.")

    def test_is_invalid_with_duplicated_unique_data(
        self,
    ):
        if getattr(self, "unique_fields"):
            self.create_instance_to_be_duplicated_on_post()

            serializer = self.get_serializer_class()(
                data=self.get_full_data(), many=False
            )
            serializer.is_valid(raise_exception=False)

            self.assertRaises(ValidationError, serializer.save)
        else:
            skip("Not applicable, model does not have any unique field.")

    def test_data_format_is_correct(self):
        instance = self.create_instance()
        serializer = self.get_serializer_class()(instance=instance, many=False)
        result = self.dict_structure_is_valid(serializer.data)
        self.assertTrue(result)

    def test_update_is_valid(self):
        instance = self.create_instance()
        serializer = self.get_serializer_class()(
            instance=instance, data=self.get_update_data(), many=False
        )
        result = serializer.is_valid(raise_exception=False)
        self.assertTrue(result)

    def test_update_is_valid_with_no_changes(self):
        instance = self.create_instance()
        _data = self.get_full_data()
        _data.update({"id": instance.id})
        serializer = self.get_serializer_class()(
            instance=instance, data=_data, many=False
        )
        result = serializer.is_valid(raise_exception=False)
        self.assertTrue(result)

    def test_partial_update_is_valid(self):
        instance = self.create_instance()
        _data = self.get_update_data()
        for key, value in _data.items():
            serializer = self.get_serializer_class()(
                instance=instance, data={key: value}, partial=True, many=False
            )
            result = serializer.is_valid(raise_exception=False)
            self.assertTrue(result)

    def test_list_correctly(self):
        baker.make(getattr(self, "model_str"), _quantity=42)
        qset = self.get_queryset()
        serializer = self.get_serializer_class()(qset, many=True)
        result = all(
            [self.dict_structure_is_valid(_item) for _item in serializer.data]
        )
        self.assertTrue(result)


class BaseAPITestCaseMixin:
    qtt = 30
    start_counter = 1
    after_create_counter = start_counter + 1
    required_fields = {}
    empty_list_response_count = 0
    authenticated_list_response_count = 1

    def tearDown(self):
        for _model in self.models_to_clean:
            _model.objects.all().delete()

    def _login(self):
        self.user, _ = get_user_model().objects.get_or_create(
            email="test@test.com"
        )
        self.client.force_authenticate(user=self.user)

    def test_empty_list_not_authenticated(self):
        response = self.client.get(self.base_url, format="json")
        self.assertEqual(HTTP_401_UNAUTHORIZED, response.status_code)

    def test_empty_list_authenticated(self):
        self.model_class.objects.all().delete()
        self._login()

        response = self.client.get(self.base_url, format="json")
        content = json.loads(response.content)
        self.assertEqual(HTTP_200_OK, response.status_code)
        self.assertEqual(self.empty_list_response_count, content.get("count"))
        self.assertEqual(None, content.get("next"))
        self.assertEqual(None, content.get("previous"))
        self.assertEqual(
            self.empty_list_response_count, len(content.get("results"))
        )

    def test_list_authenticated(self):
        self._login()

        response = self.client.get(self.base_url, format="json")

        self.assertEqual(HTTP_200_OK, response.status_code)

        content_result = json.loads(response.content)

        self.assertEqual(
            self.authenticated_list_response_count, content_result.get("count")
        )
        self.assertEqual(None, content_result.get("next"))
        self.assertEqual(None, content_result.get("previous"))

        result = content_result.get("results")[0]

        self.assert_result_and_stored(result=result, stored=self.first_element)

    def test_list_authenticated_paginated(self):
        baker.make(self.model_class_str, self.qtt)
        self._login()

        response = self.client.get(self.base_url, format="json")

        self.assertEqual(HTTP_200_OK, response.status_code)

        content_result = json.loads(response.content)

        expected_count = getattr(
            self, "list_counter", self.qtt + self.start_counter
        )
        self.assertEqual(expected_count, content_result.get("count"))
        self.assertEqual(
            "http://testserver{}?page=2".format(self.base_url),
            content_result.get("next"),
        )
        self.assertEqual(None, content_result.get("previous"))
        self.assertEqual(10, len(content_result.get("results")))

    def test_list_authenticated_paginated_page_2(self):
        baker.make(self.model_class_str, self.qtt)
        self._login()

        response = self.client.get(
            "{}?page=2".format(self.base_url), format="json"
        )

        self.assertEqual(HTTP_200_OK, response.status_code)

        content_result = json.loads(response.content)

        self.assertEqual(
            self.qtt + self.start_counter, content_result.get("count")
        )
        self.assertEqual(
            "http://testserver{}?page=3".format(self.base_url),
            content_result.get("next"),
        )
        self.assertEqual(
            "http://testserver{}".format(self.base_url),
            content_result.get("previous"),
        )
        self.assertEqual(10, len(content_result.get("results")))

    def test_create_not_authenticated(self):
        response = self.client.post(
            self.base_url,
            data=self.post_data,
            format="json",
        )
        self.assertEqual(HTTP_401_UNAUTHORIZED, response.status_code)

    def test_create_authenticated(self):
        counter = self.model_class.objects.all().count()
        self._login()
        self.assertEqual(self.start_counter, counter)

        response = self.client.post(
            self.base_url,
            data=self.post_data,
            format="json",
        )
        self.assertEqual(HTTP_201_CREATED, response.status_code)
        self.assertEqual(
            self.after_create_counter, self.model_class.objects.all().count()
        )

        result = json.loads(response.content)

        stored = self.model_class.objects.get(pk=result.get("id"))

        self.assert_result_and_stored(result=result, stored=stored)

    def test_create_missing_required_bad_request_if_any_required(
        self,
    ):
        self._login()
        _data = {
            key: value
            for key, value in self.post_data.items()
            if key not in self.required_fields
        }
        response = self.client.post(
            self.base_url,
            data=_data,
            format="json",
        )
        if self.required_fields:
            self.assertEqual(HTTP_400_BAD_REQUEST, response.status_code)
        else:
            skip("Not applicable, model does not have any required field.")

    def test_create_duplicated_unique_bad_request_if_any(
        self,
    ):
        self._login()

        _duplicated_data = copy(self.post_data)
        for key in self.unique_fields:
            _duplicated_data.update(
                {key: getattr(self.first_element, key, None)}
            )

        response = self.client.post(
            self.base_url,
            data=_duplicated_data,
            format="json",
        )
        if self.unique_fields:
            self.assertEqual(HTTP_400_BAD_REQUEST, response.status_code)
        else:
            skip("Not applicable, model does not have any unique field.")

    def test_update_authenticated(self):
        counter = self.model_class.objects.all().count()
        self._login()
        self.assertEqual(self.start_counter, counter)

        element_id = self.first_element.pk
        response = self.client.put(
            "{}{}/".format(self.base_url, element_id),
            data=self.update_data,
            format="json",
        )
        self.assertEqual(HTTP_200_OK, response.status_code)
        self.assertEqual(
            self.start_counter, self.model_class.objects.all().count()
        )

        result = json.loads(response.content)

        updated = self.model_class.objects.get(pk=element_id)

        self.assert_result_and_stored(result=result, stored=updated)

    def test_update_authenticated_ok_when_data_does_not_changes(self):
        counter = self.model_class.objects.all().count()
        self._login()
        self.assertEqual(self.start_counter, counter)

        response = self.client.put(
            "{}{}/".format(self.base_url, self.first_element.id),
            data=self.post_data,
            format="json",
        )
        self.assertEqual(HTTP_200_OK, response.status_code)
        self.assertEqual(
            self.start_counter, self.model_class.objects.all().count()
        )

        result = json.loads(response.content)

        updated = self.model_class.objects.get(pk=self.first_element.id)
        self.assert_result_and_stored(result=result, stored=updated)

    def test_update_patch_authenticated(self):
        counter = self.model_class.objects.all().count()
        self._login()
        self.assertEqual(self.start_counter, counter)

        for key, value in self.update_data.items():
            response = self.client.patch(
                "{}{}/".format(self.base_url, self.first_element.id),
                data={key: value},
                format="json",
            )
            self.assertEqual(HTTP_200_OK, response.status_code)
            self.assertEqual(
                self.start_counter, self.model_class.objects.all().count()
            )

            result = json.loads(response.content)

            updated = self.model_class.objects.get(pk=self.first_element.id)
            self.assert_result_and_stored(result=result, stored=updated)

    def test_delete_authenticated(self):
        counter = self.model_class.objects.all().count()
        self._login()
        self.assertEqual(self.start_counter, counter)

        element_id = self.first_element.pk
        response = self.client.delete(
            "{}{}/".format(self.base_url, element_id),
            format="json",
        )
        self.assertEqual(HTTP_204_NO_CONTENT, response.status_code)
        self.assertEqual(
            self.start_counter - 1, self.model_class.objects.all().count()
        )

    def test_retrieve_authenticated(self):
        self._login()

        element_id = self.first_element.pk
        response = self.client.get(
            "{}{}/".format(self.base_url, element_id),
            format="json",
        )

        self.assertEqual(HTTP_200_OK, response.status_code)

        result = json.loads(response.content)

        self.assert_result_and_stored(result=result, stored=self.first_element)


class UnitSerializerTestCase(TestCase, BaseSerializerTestCaseMixin):
    full_data = {"name": "kilogram", "abbreviation": "kg"}
    default_data = {"name": "kilogram", "abbreviation": "kg"}
    update_data = {"name": "kilogram force", "abbreviation": "kgf"}
    required_data = {"name", "abbreviation"}
    unique_fields = {"name", "abbreviation"}
    model_str = "core.Unit"
    serializer_class = UnitSerializer
    model = Unit

    def dict_structure_is_valid(self, data):
        result = True
        try:
            result = (
                result
                and isinstance(data["id"], str)
                and re.match(pattern=UUID_PATTERN, string=data["id"])
            )
            result = (
                result
                and isinstance(data["name"], str)
                and 0 < len(data["name"]) <= 255
            )
            result = (
                result
                and isinstance(data["abbreviation"], str)
                and 0 < len(data["abbreviation"]) <= 10
            )
        except:
            result = False

        return result


class IngredientSerializerTestCase(TestCase, BaseSerializerTestCaseMixin):
    full_data = {"name": "egg"}
    default_data = {"name": "egg"}
    update_data = {"name": "rice"}
    required_data = {"name"}
    unique_fields = {"name"}
    model_str = "core.Ingredient"
    serializer_class = IngredientSerializer
    model = Ingredient

    def dict_structure_is_valid(self, data):
        result = True
        try:
            result = (
                result
                and isinstance(data["id"], str)
                and re.match(pattern=UUID_PATTERN, string=data["id"])
            )
            result = (
                result
                and isinstance(data["name"], str)
                and 0 < len(data["name"]) <= 255
            )
        except:
            result = False

        return result


class RecipeIngredientSerializerTestCase(
    TestCase, BaseSerializerTestCaseMixin
):
    required_data = {"ingredient", "unit", "quantity"}
    unique_fields = {}
    model_str = "core.RecipeIngredient"
    serializer_class = RecipeIngredientSerializer
    model = RecipeIngredient

    def setUp(self):
        self.unit = baker.make("core.Unit")
        self.unit2 = baker.make("core.Unit")
        self.ingredient = baker.make("core.Ingredient")
        self.ingredient2 = baker.make("core.Ingredient")

    def get_full_data(self):
        return {
            "ingredient": {
                "id": self.ingredient.id,
                "name": self.ingredient.name,
            },
            "unit": {
                "id": self.unit.id,
                "name": self.unit.name,
                "abbreviation": self.unit.abbreviation,
            },
            "quantity": 42,
        }

    def get_default_data(self):
        return {
            "ingredient_id": self.ingredient.id,
            "unit_id": self.unit.id,
            "quantity": 42,
        }

    def get_update_data(self):
        return {
            "ingredient": {
                "id": self.ingredient2.id,
                "name": self.ingredient2.name,
            },
            "unit": {
                "id": self.unit2.id,
                "name": self.unit2.name,
                "abbreviation": self.unit2.abbreviation,
            },
            "quantity": 51,
        }

    def dict_structure_is_valid(self, data):
        result = True
        try:
            result = (
                result
                and isinstance(data["id"], str)
                and re.match(pattern=UUID_PATTERN, string=data["id"])
            )
            result = result and isinstance(data["quantity"], float)
            result = (
                result
                and isinstance(data["ingredient"]["id"], str)
                and re.match(
                    pattern=UUID_PATTERN, string=data["ingredient"]["id"]
                )
            )
            result = (
                result
                and isinstance(data["ingredient"]["name"], str)
                and 0 < len(data["ingredient"]["name"]) <= 255
            )
            result = (
                result
                and isinstance(data["unit"]["id"], str)
                and re.match(pattern=UUID_PATTERN, string=data["unit"]["id"])
            )
            result = (
                result
                and isinstance(data["unit"]["name"], str)
                and 0 < len(data["unit"]["name"]) <= 255
            )
            result = (
                result
                and isinstance(data["unit"]["abbreviation"], str)
                and 0 < len(data["unit"]["abbreviation"]) <= 10
            )
        except:
            result = False

        return result


class RecipeSerializerTestCase(TestCase, BaseSerializerTestCaseMixin):
    required_data = {"name", "serves", "preparation_time_in_minutes", "author"}
    unique_fields = {}
    model_str = "core.Recipe"
    serializer_class = RecipeSerializer
    model = Recipe
    models_to_clean = (
        Recipe,
        RecipeIngredient,
        Ingredient,
        Unit,
        get_user_model(),
    )

    def setUp(self):
        self.author, _ = get_user_model().objects.get_or_create(
            username="foobar", email="foo@foo.bar"
        )
        self.unit = baker.make("core.Unit")
        self.unit2 = baker.make("core.Unit")
        self.ingredient = baker.make("core.Ingredient")
        self.ingredient2 = baker.make("core.Ingredient")
        self.recipe_ingredient = baker.make(
            "core.RecipeIngredient", unit=self.unit, ingredient=self.ingredient
        )
        self.recipe_ingredient2 = baker.make(
            "core.RecipeIngredient",
            unit=self.unit2,
            ingredient=self.ingredient2,
        )

    def get_full_data(self):
        return {
            "name": "Recipe",
            "author": {
                "id": self.author.id,
                "email": self.author.email,
                "username": self.author.username,
            },
            "serves": 42,
            "preparation_time_in_minutes": 420,
            "preparation": "preparation steps again",
            "ingredients": [
                {
                    "id": self.recipe_ingredient.id,
                    "ingredient": {
                        "id": self.ingredient.id,
                        "name": self.ingredient.name,
                    },
                    "unit": {
                        "id": self.unit.id,
                        "name": self.unit.name,
                        "abbreviation": self.unit.abbreviation,
                    },
                    "quantity": 42,
                }
            ],
        }

    def get_default_data(self):
        return {
            "name": "Recipe",
            "author_id": self.author.id,
            "serves": 42,
            "preparation_time_in_minutes": 420,
            "preparation": "preparation steps again",
        }

    def get_update_data(self):
        return {
            "name": "Recipe revised",
            "author": {
                "id": self.author.id,
                "email": self.author.email,
                "username": self.author.username,
            },
            "serves": 51,
            "preparation_time_in_minutes": 510,
            "preparation": "preparation steps again",
            "ingredients": [
                {
                    "id": self.recipe_ingredient2.id,
                    "ingredient": {
                        "id": self.ingredient2.id,
                        "name": self.ingredient2.name,
                    },
                    "unit": {
                        "id": self.unit2.id,
                        "name": self.unit2.name,
                        "abbreviation": self.unit2.abbreviation,
                    },
                    "quantity": 51,
                }
            ],
        }

    def dict_structure_is_valid(self, data):
        result = True
        try:
            result = (
                result
                and isinstance(data["id"], str)
                and re.match(pattern=UUID_PATTERN, string=data["id"])
            )
            result = result and isinstance(data["author"]["id"], int)
            result = result and isinstance(data["author"]["username"], str)
            result = result and isinstance(data["author"]["email"], str)
            result = result and isinstance(
                data["preparation_time_in_minutes"], int
            )
            result = result and isinstance(data["preparation"], str)
            if data.get("ingredients"):
                result = (
                    result
                    and isinstance(
                        data["ingredients"][0]["ingredient"]["id"], str
                    )
                    and re.match(
                        pattern=UUID_PATTERN,
                        string=data["ingredients"][0]["ingredient"]["id"],
                    )
                )
                result = (
                    result
                    and isinstance(
                        data["ingredients"][0]["ingredient"]["name"], str
                    )
                    and 0
                    < len(data["ingredients"][0]["ingredient"]["name"])
                    <= 255
                )
                result = (
                    result
                    and isinstance(data["ingredients"][0]["unit"]["id"], str)
                    and re.match(
                        pattern=UUID_PATTERN,
                        string=data["ingredients"][0]["unit"]["id"],
                    )
                )
                result = (
                    result
                    and isinstance(data["ingredients"][0]["unit"]["name"], str)
                    and 0 < len(data["ingredients"][0]["unit"]["name"]) <= 255
                )
                result = (
                    result
                    and isinstance(
                        data["ingredients"][0]["unit"]["abbreviation"], str
                    )
                    and 0
                    < len(data["ingredients"][0]["unit"]["abbreviation"])
                    <= 10
                )
        except:
            result = False

        return result


class UnitViewSetTestCase(TestCase, BaseAPITestCaseMixin):
    def setUp(self):
        self.required_fields = {"name", "abbreviation"}
        self.unique_fields = (
            "name",
            "abbreviation",
        )
        self.base_url = "/api/units/"
        self.model_class_str = "core.Unit"
        self.model_class = Unit

        self.client = APIClient()
        self.first_element = self.model_class.objects.create(
            name="gram", abbreviation="g"
        )

        self.post_data = {"name": "kilogram", "abbreviation": "kg"}
        self.update_data = {"name": "kilogram force", "abbreviation": "kgf"}

        self.user, _ = get_user_model().objects.get_or_create(
            email="test@test.com"
        )
        self.models_to_clean = (Unit, get_user_model())

    def assert_result_and_stored(self, stored, result):
        self.assertEqual(str(stored.id), result.get("id"))
        self.assertEqual(stored.abbreviation, result.get("abbreviation"))
        self.assertEqual(stored.name, result.get("name"))


class IngredientViewSetTestCase(TestCase, BaseAPITestCaseMixin):
    def setUp(self):
        self.required_fields = {"name"}
        self.unique_fields = ("name",)
        self.base_url = "/api/ingredients/"
        self.model_class_str = "core.Ingredient"
        self.model_class = Ingredient

        self.client = APIClient()
        self.first_element = self.model_class.objects.create(name="rice")

        self.post_data = {"name": "cheese"}
        self.update_data = {"name": "parmesan"}

        self.user, _ = get_user_model().objects.get_or_create(
            email="test@test.com"
        )
        self.models_to_clean = (Unit, get_user_model())

    def assert_result_and_stored(self, stored, result):
        self.assertEqual(str(stored.id), result.get("id"))
        self.assertEqual(stored.name, result.get("name"))


class RecipeViewSetSetTestCase(TestCase, BaseAPITestCaseMixin):
    def setUp(self):
        self.required_fields = {
            "name",
            "serves",
            "preparation_time_in_minutes",
            "preparation",
            "author",
        }
        self.unique_fields = {}
        self.base_url = "/api/recipes/"
        self.model_class_str = "core.Recipe"
        self.model_class = Recipe

        self.unit = baker.make("core.Unit")
        self.unit2 = baker.make("core.Unit")
        self.ingredient = baker.make("core.Ingredient")
        self.ingredient2 = baker.make("core.Ingredient")

        self.user, _ = get_user_model().objects.get_or_create(
            email="test@test.com", username="foo"
        )

        self.client = APIClient()
        self.first_element = self.model_class.objects.create(
            name="cheese pizza",
            serves=4,
            preparation="prep",
            preparation_time_in_minutes=15,
            author=self.user,
        )

        self.post_data = {
            "name": "cheese pizza",
            "serves": 4,
            "preparation_time_in_minutes": 30,
            "preparation": "bake it",
            "author": {
                "id": self.user.id,
                "username": self.user.username,
                "email": self.user.email,
            },
            "ingredients": [
                {
                    "ingredient": {
                        "id": self.ingredient.id,
                        "name": self.ingredient.name,
                    },
                    "unit": {
                        "id": self.unit.id,
                        "name": self.unit.name,
                        "abbreviation": self.unit.abbreviation,
                    },
                    "quantity": 42,
                }
            ],
        }
        self.update_data = {
            "name": "cheesier pizza",
            "serves": 8,
            "preparation_time_in_minutes": 60,
            "preparation": "bake it again",
            "author": {
                "id": self.user.id,
                "username": self.user.username,
                "email": self.user.email,
            },
            "ingredients": [
                {
                    "ingredient": {
                        "id": self.ingredient.id,
                        "name": self.ingredient.name,
                    },
                    "unit": {
                        "id": self.unit.id,
                        "name": self.unit.name,
                        "abbreviation": self.unit.abbreviation,
                    },
                    "quantity": 42,
                },
                {
                    "ingredient": {
                        "name": "Bigger Cheese",
                    },
                    "unit": {
                        "id": self.unit.id,
                        "name": self.unit.name,
                        "abbreviation": self.unit.abbreviation,
                    },
                    "quantity": 420,
                },
            ],
        }
        self.models_to_clean = (
            Unit,
            Ingredient,
            RecipeIngredient,
            Recipe,
            get_user_model(),
        )

    def assert_result_and_stored(self, stored, result):
        self.assertEqual(str(stored.id), result.get("id"))
        self.assertEqual(stored.name, result.get("name"))
        self.assertEqual(stored.serves, result.get("serves"))
        self.assertEqual(
            stored.preparation_time_in_minutes,
            result.get("preparation_time_in_minutes"),
        )
        self.assertEqual(stored.preparation, result.get("preparation"))
        self.assertEqual(stored.author.id, result.get("author").get("id"))
        self.assertEqual(
            stored.ingredients.all().count(), len(result.get("ingredients"))
        )
