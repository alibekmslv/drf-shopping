import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from shopping_list.models import ShoppingItem, ShoppingList, User


@pytest.fixture(scope='session')
def create_shopping_item():
    def _create_shopping_item(name, user):
        shopping_list = ShoppingList.objects.create(name='My shopping list')
        shopping_list.members.add(user)
        shopping_item = ShoppingItem.objects.create(
            name=name, purchased=False, shopping_list=shopping_list
        )

        return shopping_item

    return _create_shopping_item


@pytest.fixture(scope='session')
def create_shopping_item_and_add_to_shopping_list():
    def _create_shopping_item_to_existing_shopping_list(name, user, shopping_list):
        shopping_item = ShoppingItem.objects.create(
            name=name, purchased=False, shopping_list=shopping_list
        )

        return shopping_item

    return _create_shopping_item_to_existing_shopping_list


@pytest.fixture(scope="session")
def create_user():
    def _create_user(username='alice'):
        return User.objects.create_user(
            username=username, email=f"{username}@test.com", password="foo"
        )

    return _create_user


@pytest.fixture(scope="session")
def create_authenticated_client():
    def _create_authenticated_client(user):
        client = APIClient()
        client.force_login(user)

        return client

    return _create_authenticated_client


@pytest.fixture(scope="session")
def create_token_authenticated_client():
    def _create_token_authenticated_client(user, password='foo'):
        client = APIClient()
        token_url = reverse('api-token-auth')
        data = {
            'username': user.username,
            'password': password,
        }

        token_response = client.post(token_url, data=data, format='json')
        token = token_response.data['token']
        client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        return client

    return _create_token_authenticated_client


@pytest.fixture(scope="session")
def create_shopping_list():
    def _create_shopping_list(user, name='Groceries'):
        shopping_list = ShoppingList.objects.create(name=name)
        shopping_list.members.add(user)

        return shopping_list

    return _create_shopping_list
