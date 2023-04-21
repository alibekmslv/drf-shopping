import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from shopping_list.models import ShoppingList, ShoppingItem, User


@pytest.mark.django_db
def test_valid_user_is_created(create_user):
    user_alice = create_user()
    user_bob = create_user(username='bob')
    user_charlie = create_user(username='charlie')

    assert user_alice.username == 'alice'
    assert user_alice.email == 'alice@test.com'
    assert user_bob.username == 'bob'
    assert user_bob.email == 'bob@test.com'
    assert user_charlie.username == 'charlie'
    assert user_charlie.email == 'charlie@test.com'


@pytest.mark.django_db
def test_call_with_token_authentication(create_user):
    user_alice = create_user()

    client = APIClient()
    token_url = reverse('api-token-auth')

    data = {
        'username': 'alice',
        'password': 'foo',
    }

    token_response = client.post(token_url, data=data, format='json')
    token = token_response.data['token']

    url = reverse('all-shopping-lists')
    client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_call_with_token_authentication_function(create_user, create_token_authenticated_client):
    user_alice = create_user()

    client = create_token_authenticated_client(user_alice)

    url = reverse('all-shopping-lists')
    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
