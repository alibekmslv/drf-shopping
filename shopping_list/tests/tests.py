from datetime import datetime, timedelta
from unittest import mock
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from shopping_list.models import ShoppingList, ShoppingItem, User


@pytest.mark.django_db
def test_valid_shopping_list_is_created(create_user, create_authenticated_client):
    url = reverse('all-shopping-lists')
    data = {
        'name': 'Groceries',
    }
    client = create_authenticated_client(create_user())
    response = client.post(url, data, format='json')

    assert response.status_code == status.HTTP_201_CREATED
    assert ShoppingList.objects.get().name == 'Groceries'


@pytest.mark.django_db
def test_shopping_list_name_missing_returns_bad_request(create_user, create_authenticated_client):
    user_alice = create_user()
    client = create_authenticated_client(user_alice)

    url = reverse('all-shopping-lists')

    data = {
        'something_else': 'blahblahblah',
    }

    response = client.post(url, data, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST


# 1. Shopping list
#    1. list enpoint
#    2. retrieve enpoint
#    3. update enpoint
#    4. delete enpoint


# SHOPPING LIST LIST
@pytest.mark.django_db
def test_client_retrieves_only_shopping_lists_they_are_member_of(
    create_user, create_shopping_list, create_authenticated_client
):
    user_alice = create_user()
    user_bob = create_user(username='charlie')

    client = create_authenticated_client(user_bob)

    shopping_list = create_shopping_list(user_alice)
    another_shopping_list = create_shopping_list(user_bob, name='Books')

    url = reverse('all-shopping-lists')

    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['name'] == 'Books'


@pytest.mark.django_db
def test_max_3_shopping_items_on_shopping_list(
    create_user, create_authenticated_client, create_shopping_list
):
    user_alice = create_user()
    client = create_authenticated_client(user=user_alice)

    shopping_list = create_shopping_list(user=user_alice)
    ShoppingItem.objects.create(shopping_list=shopping_list, name='Eggs', purchased=False)
    ShoppingItem.objects.create(shopping_list=shopping_list, name='Chocolate', purchased=False)
    ShoppingItem.objects.create(shopping_list=shopping_list, name='Milk', purchased=False)
    ShoppingItem.objects.create(shopping_list=shopping_list, name='Mango', purchased=False)

    url = reverse('shopping-list-detail', args=[shopping_list.id])

    response = client.get(url)

    assert len(response.data['unpurchased_items']) == 3


@pytest.mark.django_db
def test_all_shopping_items_on_shopping_list_unpurchased(
    create_user, create_authenticated_client, create_shopping_list
):
    user_alice = create_user()
    client = create_authenticated_client(user=user_alice)

    shopping_list = create_shopping_list(user=user_alice)
    ShoppingItem.objects.create(shopping_list=shopping_list, name='Eggs', purchased=False)
    ShoppingItem.objects.create(shopping_list=shopping_list, name='Chocolate', purchased=True)
    ShoppingItem.objects.create(shopping_list=shopping_list, name='Milk', purchased=False)

    url = reverse('shopping-list-detail', args=[shopping_list.id])

    response = client.get(url)

    assert len(response.data['unpurchased_items']) == 2


# SHOPPING LIST RETRIEVE
@pytest.mark.django_db
def test_shopping_list_is_retrieved_by_id(
    create_user, create_shopping_list, create_authenticated_client
):
    user_alice = create_user()
    client = create_authenticated_client(user_alice)
    shopping_list = create_shopping_list(user_alice)

    url = reverse('shopping-list-detail', args=[shopping_list.id])

    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data['name'] == 'Groceries'


@pytest.mark.django_db
def test_shopping_list_includes_only_corresponding_items(
    create_user, create_shopping_list, create_authenticated_client
):
    user = create_user()
    client = create_authenticated_client(user)
    shopping_list = create_shopping_list(user)
    another_shopping_list = ShoppingList.objects.create(name='Books')
    another_shopping_list.members.add(user)

    ShoppingItem.objects.create(shopping_list=shopping_list, name='Eggs', purchased=False)
    ShoppingItem.objects.create(
        shopping_list=another_shopping_list, name='The seven sisters', purchased=False
    )

    url = reverse('shopping-list-detail', args=[shopping_list.id])

    response = client.get(url)

    assert len(response.data['unpurchased_items']) == 1
    assert response.data['unpurchased_items'][0]['name'] == 'Eggs'


@pytest.mark.django_db
def test_admin_can_retrieve_shopping_list(create_user, create_shopping_list, admin_client):
    user = create_user()
    shopping_list = create_shopping_list(user)

    url = reverse('shopping-list-detail', args=[shopping_list.id])

    response = admin_client.get(url)

    assert response.status_code == status.HTTP_200_OK


# SHOPPING LIST UPDATE
@pytest.mark.django_db
def test_shopping_list_name_is_changed(
    create_user, create_shopping_list, create_authenticated_client
):
    user = create_user()
    client = create_authenticated_client(user)
    shopping_list = create_shopping_list(user)

    url = reverse('shopping-list-detail', args=[shopping_list.id])

    data = {
        'name': 'Food',
    }

    response = client.put(url, data=data, format='json')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['name'] == 'Food'


@pytest.mark.django_db
def test_update_shopping_list_restricted_if_not_member(
    create_user, create_shopping_list, create_authenticated_client
):
    user = create_user()
    client = create_authenticated_client(user)

    shopping_list_creator = User.objects.create_user(
        'ShoppingListCreator', 'foo@foo.com', 'password'
    )
    shopping_list = create_shopping_list(shopping_list_creator)

    url = reverse('shopping-list-detail', args=[shopping_list.id])

    data = {
        'name': 'Food',
    }

    response = client.put(url, data=data, format='json')

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_partial_update_shopping_list_restricted_if_not_member(
    create_user, create_shopping_list, create_authenticated_client
):
    user = create_user()
    client = create_authenticated_client(user)

    shopping_list_creator = User.objects.create_user(
        'ShoppingListCreator', 'foo@foo.com', 'password'
    )
    shopping_list = create_shopping_list(shopping_list_creator)

    url = reverse('shopping-list-detail', args=[shopping_list.id])

    data = {
        'name': 'Food',
    }

    response = client.patch(url, data=data, format='json')

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_shopping_list_not_changed_because_name_missing(
    create_user, create_shopping_list, create_authenticated_client
):
    user = create_user()
    client = create_authenticated_client(user)
    shopping_list = create_shopping_list(user)

    url = reverse('shopping-list-detail', args=[shopping_list.id])

    data = {
        'something_else': 'blahblah',
    }

    response = client.put(url, data=data, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_shopping_list_name_is_changed_with_partial_update(
    create_user, create_shopping_list, create_authenticated_client
):
    user = create_user()
    client = create_authenticated_client(user)
    shopping_list = create_shopping_list(user)

    url = reverse('shopping-list-detail', args=[shopping_list.id])

    data = {
        'name': 'Food',
    }

    response = client.patch(url, data=data, format='json')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['name'] == 'Food'


@pytest.mark.django_db
def test_shopping_list_partial_update_with_missing_name_has_no_impact(
    create_user, create_shopping_list, create_authenticated_client
):
    user = create_user()
    client = create_authenticated_client(user)
    shopping_list = create_shopping_list(user)

    url = reverse('shopping-list-detail', args=[shopping_list.id])

    data = {
        'something_else': 'Food',
    }

    response = client.patch(url, data=data, format='json')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['name'] == 'Groceries'


# SHOPPING LIST DELETE
@pytest.mark.django_db
def test_shopping_list_is_deleted(create_user, create_authenticated_client, create_shopping_list):
    user = create_user()
    client = create_authenticated_client(user)
    shopping_list = create_shopping_list(user)

    url = reverse('shopping-list-detail', args=[shopping_list.id])

    response = client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert len(ShoppingList.objects.all()) == 0


@pytest.mark.django_db
def test_delete_shopping_list_restricted_if_not_member(
    create_user, create_authenticated_client, create_shopping_list
):
    user = create_user()
    client = create_authenticated_client(user)

    shopping_list_creator = User.objects.create_user(
        'ShoppingListCreator', 'foo@foo.com', 'password'
    )
    shopping_list = create_shopping_list(shopping_list_creator)

    url = reverse('shopping-list-detail', args=[shopping_list.id])

    response = client.delete(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN


# 1. Shopping item
#    1. create enpoint
#    2. retrieve enpoint
#    3. update enpoint
#    4. delete enpoint


# SHOPPING ITEM CREATE
@pytest.mark.django_db
def test_valid_shopping_item_is_created(
    create_user, create_authenticated_client, create_shopping_list
):
    user = create_user()
    client = create_authenticated_client(user)
    shopping_list = create_shopping_list(user)

    url = reverse('list-add-shopping-item', args=[shopping_list.id])

    data = {
        'name': 'Milk',
        'purchased': False,
    }

    response = client.post(url, data, format='json')

    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_valid_shopping_item_missing_data_returns_bad_request(
    create_user, create_authenticated_client, create_shopping_list
):
    user = create_user()
    client = create_authenticated_client(user)
    shopping_list = create_shopping_list(user)

    url = reverse('list-add-shopping-item', args=[shopping_list.id])

    data = {
        'name': 'Milk',
    }

    response = client.post(url, data, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_not_member_of_list_can_not_add_shopping_item(
    create_user, create_shopping_list, create_authenticated_client
):
    user = create_user()
    client = create_authenticated_client(user)

    shopping_list_creator = User.objects.create_user("creator", "creator@list.com", "password")
    shopping_list = create_shopping_list(shopping_list_creator)

    url = reverse('list-add-shopping-item', args=[shopping_list.id])

    data = {
        'name': 'Milk',
        'purchased': False,
    }

    response = client.post(url, data=data, format='json')

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_admin_can_add_shopping_items(create_user, create_shopping_list, admin_client):
    user = create_user()
    shopping_list = create_shopping_list(user)

    url = reverse('list-add-shopping-item', args=[shopping_list.id])

    data = {
        'name': 'Milk',
        'purchased': False,
    }

    response = admin_client.post(url, data, format='json')

    assert response.status_code == status.HTTP_201_CREATED


# SHOPPING ITEM RETRIEVE
@pytest.mark.django_db
def test_shopping_item_is_retrieved_by_id(
    create_user, create_authenticated_client, create_shopping_item
):
    user = create_user()
    client = create_authenticated_client(user)
    shopping_item = create_shopping_item(name='Chocolate', user=user)

    url = reverse(
        'shopping-item-detail',
        kwargs={
            'pk': shopping_item.shopping_list.id,
            'item_pk': shopping_item.id,
        },
    )

    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data['name'] == 'Chocolate'


@pytest.mark.django_db
def test_shopping_item_detail_access_restricted_if_not_member_of_shopping_list(
    create_user, create_authenticated_client, create_shopping_item
):
    user_alice = create_user()
    user_charlie = create_user(username='charlie')

    client = create_authenticated_client(user_charlie)

    shopping_item = create_shopping_item(name='Chocolate', user=user_alice)

    url = reverse(
        'shopping-item-detail',
        kwargs={'pk': shopping_item.shopping_list.id, 'item_pk': shopping_item.id},
    )

    response = client.get(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_admin_can_retrieve_single_shopping_item(create_user, create_shopping_item, admin_client):
    user_alice = create_user()
    shopping_item = create_shopping_item(name='Chocolate', user=user_alice)

    url = reverse(
        'shopping-item-detail',
        kwargs={'pk': shopping_item.shopping_list.id, 'item_pk': shopping_item.id},
    )

    response = admin_client.get(url)

    assert response.status_code == status.HTTP_200_OK


# SHOPPING ITEM UPDATE
@pytest.mark.django_db
def test_change_shopping_item_purchased_status(
    create_user, create_authenticated_client, create_shopping_item
):
    user_alice = create_user()
    client = create_authenticated_client(user_alice)
    shopping_item = create_shopping_item(name='Chocolate', user=user_alice)

    url = reverse(
        'shopping-item-detail',
        kwargs={
            'pk': shopping_item.shopping_list.id,
            'item_pk': shopping_item.id,
        },
    )

    data = {
        'name': 'Chocolate',
        'purchased': True,
    }

    response = client.put(url, data, format='json')

    assert response.status_code == status.HTTP_200_OK
    assert ShoppingItem.objects.get().purchased is True


@pytest.mark.django_db
def test_change_shopping_item_purchased_status_with_missing_data_returns_bad_request(
    create_user,
    create_authenticated_client,
    create_shopping_item,
):
    user = create_user()
    client = create_authenticated_client(user)
    shopping_item = create_shopping_item(name='Chocolate', user=user)

    url = reverse(
        'shopping-item-detail',
        kwargs={
            'pk': shopping_item.shopping_list.id,
            'item_pk': shopping_item.id,
        },
    )

    data = {
        'purchased': True,
    }

    response = client.put(url, data, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_change_shopping_item_purchased_status_with_partial_update(
    create_user, create_authenticated_client, create_shopping_item
):
    user = create_user()
    client = create_authenticated_client(user)
    shopping_item = create_shopping_item(name='Chocolate', user=user)

    url = reverse(
        'shopping-item-detail',
        kwargs={
            'pk': shopping_item.shopping_list.id,
            'item_pk': shopping_item.id,
        },
    )

    data = {
        'purchased': True,
    }

    response = client.patch(url, data, format='json')

    assert response.status_code == status.HTTP_200_OK
    assert ShoppingItem.objects.get().purchased is True


@pytest.mark.django_db
def test_shopping_item_partial_update_with_missing_data_has_no_impact(
    create_user, create_authenticated_client, create_shopping_item
):
    user = create_user()
    client = create_authenticated_client(user)
    shopping_item = create_shopping_item(name='Chocolate', user=user)

    url = reverse(
        'shopping-item-detail',
        kwargs={
            'pk': shopping_item.shopping_list.id,
            'item_pk': shopping_item.id,
        },
    )

    data = {
        'something_else': True,
    }

    response = client.patch(url, data, format='json')

    assert response.status_code == status.HTTP_200_OK
    assert ShoppingItem.objects.get().purchased is False


@pytest.mark.django_db
def test_shopping_item_update_restricted_if_not_member_of_shopping_list(
    create_user, create_shopping_item, create_authenticated_client
):
    user_alice = create_user()
    user_charlie = create_user(username='charlie')

    client = create_authenticated_client(user_charlie)

    shopping_item = create_shopping_item(name='Chocolate', user=user_alice)

    url = reverse(
        'shopping-item-detail',
        kwargs={'pk': shopping_item.shopping_list.id, 'item_pk': shopping_item.id},
    )

    data = {
        'name': 'Chocolate',
        'purchased': True,
    }

    response = client.put(url, data=data, format='json')

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_shopping_item_partial_update_restricted_if_not_member_of_shopping_list(
    create_user, create_shopping_item, create_authenticated_client
):
    user_alice = create_user()
    user_charlie = create_user(username='charlie')

    client = create_authenticated_client(user_charlie)

    shopping_item = create_shopping_item(name='Chocolate', user=user_alice)

    url = reverse(
        'shopping-item-detail',
        kwargs={'pk': shopping_item.shopping_list.id, 'item_pk': shopping_item.id},
    )

    data = {
        'purchased': False,
    }

    response = client.patch(url, data=data, format='json')

    assert response.status_code == status.HTTP_403_FORBIDDEN


# SHOPPING ITEM DELETE
@pytest.mark.django_db
def test_shopping_item_is_deleted(create_user, create_authenticated_client, create_shopping_item):
    user = create_user()
    client = create_authenticated_client(user)
    shopping_item = create_shopping_item(name='Chocolate', user=user)

    url = reverse(
        'shopping-item-detail',
        kwargs={
            'pk': shopping_item.shopping_list.id,
            'item_pk': shopping_item.id,
        },
    )

    response = client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert len(ShoppingItem.objects.all()) == 0


@pytest.mark.django_db
def test_shopping_item_delete_restricted_if_not_member_of_shopping_list(
    create_user, create_authenticated_client, create_shopping_item
):
    user_alice = create_user()
    user_charlie = create_user(username='charlie')

    client = create_authenticated_client(user_charlie)

    shopping_item = create_shopping_item(name='Chocolate', user=user_alice)

    url = reverse(
        'shopping-item-detail',
        kwargs={
            'pk': shopping_item.shopping_list.id,
            'item_pk': shopping_item.id,
        },
    )

    response = client.delete(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert len(ShoppingItem.objects.all()) == 1


@pytest.mark.django_db
def test_list_shopping_items_is_retrieved_by_shopping_list_member(
    create_user, create_authenticated_client, create_shopping_list
):
    user_alice = create_user()
    shopping_list = create_shopping_list(user=user_alice)
    shopping_item_1 = ShoppingItem.objects.create(
        name='Oranges', purchased=False, shopping_list=shopping_list
    )
    shopping_item_2 = ShoppingItem.objects.create(
        name='Milk', purchased=False, shopping_list=shopping_list
    )

    client = create_authenticated_client(user_alice)
    url = reverse('list-add-shopping-item', kwargs={'pk': shopping_list.id})
    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['results']) == 2
    assert response.data['results'][0]['name'] == shopping_item_1.name
    assert response.data['results'][1]['name'] == shopping_item_2.name


@pytest.mark.django_db
def test_not_member_can_not_retrieve_shopping_items(
    create_user, create_authenticated_client, create_shopping_item
):
    user_alice = create_user()
    shopping_item = create_shopping_item('Oranges', user_alice)

    user_charlie = create_user(username='charlie')
    client = create_authenticated_client(user_charlie)

    url = reverse('list-add-shopping-item', kwargs={'pk': shopping_item.shopping_list.id})

    response = client.get(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_list_shopping_items_only_the_ones_belonging_to_the_same_shopping_list(
    create_user, create_authenticated_client, create_shopping_list, create_shopping_item
):
    user_alice = create_user()

    shopping_list_1 = create_shopping_list(user_alice)
    shopping_item_1 = ShoppingItem.objects.create(
        name='Oranges', purchased=False, shopping_list=shopping_list_1
    )

    # create_shopping_item('Oran')

    shopping_list_2 = create_shopping_list(user_alice)
    shopping_item_2 = ShoppingItem.objects.create(
        name='Milk', purchased=False, shopping_list=shopping_list_2
    )

    client = create_authenticated_client(user_alice)
    url = reverse('list-add-shopping-item', kwargs={'pk': shopping_list_1.id})

    response = client.get(url)

    assert len(response.data['results']) == 1
    assert response.data['results'][0]['name'] == shopping_item_1.name


@pytest.mark.django_db
def test_duplicate_item_on_list_bad_request(
    create_user, create_authenticated_client, create_shopping_list
):
    user_alice = create_user()
    client = create_authenticated_client(user=user_alice)

    shopping_list = create_shopping_list(user_alice)

    ShoppingItem.objects.create(name='Milk', purchased=False, shopping_list=shopping_list)

    url = reverse('list-add-shopping-item', args=[shopping_list.id])

    data = {
        'name': 'Milk',
        'purchased': False,
    }

    response = client.post(url, data=data, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert len(shopping_list.shopping_items.all()) == 1


@pytest.mark.django_db
def test_correct_order_shopping_lists(
    create_user, create_authenticated_client, create_shopping_list
):
    url = reverse('all-shopping-lists')
    user_alice = create_user()
    client = create_authenticated_client(user=user_alice)

    old_time = datetime.now() - timedelta(days=1)
    older_time = datetime.now() - timedelta(days=100)

    with mock.patch('django.utils.timezone.now') as mock_now:
        mock_now.return_value = old_time
        create_shopping_list(user=user_alice, name='Old')

        mock_now.return_value = older_time
        create_shopping_list(user=user_alice, name='Older')

    create_shopping_list(user=user_alice, name='New')

    response = client.get(url)

    assert response.data['results'][0]['name'] == 'New'
    assert response.data['results'][1]['name'] == 'Old'
    assert response.data['results'][2]['name'] == 'Older'


@pytest.mark.django_db
def test_shopping_lists_order_changed_when_item_marked_purchased(
    create_user, create_authenticated_client, create_shopping_list
):
    user_alice = create_user()
    client = create_authenticated_client(user=user_alice)

    more_recent_time = datetime.now() - timedelta(days=1)
    older_time = datetime.now() - timedelta(days=20)

    with mock.patch('django.utils.timezone.now') as mock_now:
        mock_now.return_value = older_time
        older_list = create_shopping_list(user=user_alice, name='Older')
        shopping_item_on_older_list = ShoppingItem.objects.create(
            name='Milk', purchased=False, shopping_list=older_list
        )

        mock_now.return_value = more_recent_time
        more_recent_list = create_shopping_list(user=user_alice, name='Recent')

    shopping_item_url = reverse(
        'shopping-item-detail',
        kwargs={'pk': older_list.id, 'item_pk': shopping_item_on_older_list.id},
    )
    shopping_lists_url = reverse('all-shopping-lists')

    data = {
        'purchased': True,
    }
    client.patch(shopping_item_url, data=data, format='json')

    response = client.get(shopping_lists_url)

    assert response.data['results'][0]['name'] == 'Older'
    assert response.data['results'][1]['name'] == 'Recent'


@pytest.mark.django_db
def test_add_members_list_member(create_user, create_authenticated_client, create_shopping_list):
    user_alice = create_user()
    client = create_authenticated_client(user=user_alice)
    shopping_list = create_shopping_list(user=user_alice)

    user_bob = create_user(username='bob')
    user_charlie = create_user(username='charlie')

    data = {'members': [user_bob.id, user_charlie.id]}

    url = reverse('shopping-list-add-members', args=[shopping_list.id])

    response = client.put(url, data=data, format='json')

    assert len(response.data['members']) == 3
    assert user_alice.id in response.data['members']
    assert user_bob.id in response.data['members']
    assert user_charlie.id in response.data['members']


@pytest.mark.django_db
def test_add_members_not_list_member(
    create_user, create_authenticated_client, create_shopping_list
):
    user_alice = create_user()
    shopping_list = create_shopping_list(user=user_alice)

    user_charlie = create_user(username='charlie')
    client_charlie = create_authenticated_client(user=user_charlie)

    data = {'members': [user_charlie.id]}

    url = reverse('shopping-list-add-members', args=[shopping_list.id])

    response = client_charlie.put(url, data=data, format='json')

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_add_members_wrong_data(create_user, create_authenticated_client, create_shopping_list):
    user_alice = create_user()
    client_alice = create_authenticated_client(user=user_alice)
    shopping_list = create_shopping_list(user=user_alice)

    data = {'members': [777]}

    url = reverse('shopping-list-add-members', args=[shopping_list.id])

    response = client_alice.put(url, data=data, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_remove_members_list_member(create_user, create_authenticated_client, create_shopping_list):
    user_alice = create_user()
    user_bob = create_user(username='bob')
    user_charlie = create_user(username='charlie')

    client_alice = create_authenticated_client(user=user_alice)
    shopping_list = create_shopping_list(user=user_alice)

    shopping_list.members.add(user_bob)
    shopping_list.members.add(user_charlie)

    data = {'members': [user_charlie.id]}

    url = reverse('shopping-list-remove-members', args=[shopping_list.id])

    response = client_alice.put(url, data=data, format='json')

    assert len(response.data['members']) == 2
    assert user_alice.id in response.data['members']
    assert user_bob.id in response.data['members']
    assert user_charlie.id not in response.data['members']


@pytest.mark.django_db
def test_remove_members_not_list_member(
    create_user, create_authenticated_client, create_shopping_list
):
    user_alice = create_user()
    shopping_list = create_shopping_list(user=user_alice)

    user_charlie = create_user(username='charlie')
    client_charlie = create_authenticated_client(user=user_charlie)

    data = {'members': [user_alice.id]}

    url = reverse('shopping-list-remove-members', args=[shopping_list.id])

    response = client_charlie.put(url, data=data, format='json')

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_remove_members_wrong_data(create_user, create_authenticated_client, create_shopping_list):
    user_alice = create_user()
    client_alice = create_authenticated_client(user=user_alice)
    shopping_list = create_shopping_list(user=user_alice)

    data = {'members': [777]}

    url = reverse('shopping-list-remove-members', args=[shopping_list.id])

    response = client_alice.put(url, data=data, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_search_returns_corresponding_items(
    create_user, create_authenticated_client, create_shopping_item
):
    user_alice = create_user()
    client_alice = create_authenticated_client(user=user_alice)

    create_shopping_item(name='Chocolate', user=user_alice)
    create_shopping_item(name='Skim milk', user=user_alice)

    search_param = "?search=milk"
    url = reverse("search-shopping-items") + search_param

    response = client_alice.get(url)

    assert len(response.data['results']) == 1
    assert response.data['results'][0]['name'] == 'Skim milk'


@pytest.mark.django_db
def test_search_returns_only_users_results(
    create_user, create_authenticated_client, create_shopping_item
):
    user_alice = create_user()
    user_charlie = create_user(username='charlie')

    create_shopping_item(name='Milk', user=user_alice)
    create_shopping_item(name='Milk', user=user_charlie)

    client_charlie = create_authenticated_client(user=user_charlie)

    search_param = "?search=milk"
    url = reverse("search-shopping-items") + search_param

    response = client_charlie.get(url)

    assert len(response.data['results']) == 1


@pytest.mark.django_db
def test_order_shopping_items_names_ascending(
    create_user,
    create_authenticated_client,
    create_shopping_list,
    create_shopping_item_and_add_to_shopping_list,
):
    user_alice = create_user()
    client_alice = create_authenticated_client(user=user_alice)

    shopping_list = create_shopping_list(user=user_alice)

    create_shopping_item_and_add_to_shopping_list(
        name='Bananas', user=user_alice, shopping_list=shopping_list
    )
    create_shopping_item_and_add_to_shopping_list(
        name='Apples', user=user_alice, shopping_list=shopping_list
    )

    order_param = "?ordering=name"
    url = reverse('list-add-shopping-item', args=[shopping_list.id]) + order_param

    response = client_alice.get(url)

    assert response.data['results'][0]['name'] == 'Apples'
    assert response.data['results'][1]['name'] == 'Bananas'


@pytest.mark.django_db
def test_order_shopping_items_names_descending(
    create_user,
    create_authenticated_client,
    create_shopping_list,
    create_shopping_item_and_add_to_shopping_list,
):
    user_alice = create_user()
    client_alice = create_authenticated_client(user=user_alice)

    shopping_list = create_shopping_list(user=user_alice)

    create_shopping_item_and_add_to_shopping_list(
        name='Apples', user=user_alice, shopping_list=shopping_list
    )
    create_shopping_item_and_add_to_shopping_list(
        name='Bananas', user=user_alice, shopping_list=shopping_list
    )

    order_param = "?ordering=-name"
    url = reverse('list-add-shopping-item', args=[shopping_list.id]) + order_param

    response = client_alice.get(url)

    assert response.data['results'][0]['name'] == 'Bananas'
    assert response.data['results'][1]['name'] == 'Apples'


@pytest.mark.django_db
def test_order_shopping_items_unpurchased_first(
    create_user,
    create_authenticated_client,
    create_shopping_list,
    create_shopping_item_and_add_to_shopping_list,
):
    user_alice = create_user()
    client_alice = create_authenticated_client(user=user_alice)

    shopping_list = create_shopping_list(user=user_alice)

    ShoppingItem.objects.create(name="Apples", purchased=False, shopping_list=shopping_list)
    ShoppingItem.objects.create(name="Bananas", purchased=True, shopping_list=shopping_list)

    order_param = "?ordering=purchased"
    url = reverse('list-add-shopping-item', args=[shopping_list.id]) + order_param

    response = client_alice.get(url)

    assert response.data['results'][0]['name'] == 'Apples'
    assert response.data['results'][1]['name'] == 'Bananas'


@pytest.mark.django_db
def test_order_shopping_items_purchased_first(
    create_user,
    create_authenticated_client,
    create_shopping_list,
    create_shopping_item_and_add_to_shopping_list,
):
    user_alice = create_user()
    client_alice = create_authenticated_client(user=user_alice)

    shopping_list = create_shopping_list(user=user_alice)

    ShoppingItem.objects.create(name="Apples", purchased=False, shopping_list=shopping_list)
    ShoppingItem.objects.create(name="Bananas", purchased=True, shopping_list=shopping_list)

    order_param = "?ordering=-purchased"
    url = reverse('list-add-shopping-item', args=[shopping_list.id]) + order_param

    response = client_alice.get(url)

    assert response.data['results'][0]['name'] == 'Bananas'
    assert response.data['results'][1]['name'] == 'Apples'


@pytest.mark.django_db
def test_order_shopping_items_purchased_and_names(
    create_user,
    create_authenticated_client,
    create_shopping_list,
    create_shopping_item_and_add_to_shopping_list,
):
    user_alice = create_user()
    client_alice = create_authenticated_client(user=user_alice)

    shopping_list = create_shopping_list(user=user_alice)

    ShoppingItem.objects.create(name="Apples", purchased=True, shopping_list=shopping_list)
    ShoppingItem.objects.create(name="Bananas", purchased=False, shopping_list=shopping_list)
    ShoppingItem.objects.create(name="Coconut", purchased=True, shopping_list=shopping_list)
    ShoppingItem.objects.create(name="Dates", purchased=False, shopping_list=shopping_list)

    order_param = "?ordering=purchased,names"
    url = reverse('list-add-shopping-item', args=[shopping_list.id]) + order_param

    response = client_alice.get(url)

    assert response.data['results'][0]['name'] == 'Bananas'
    assert response.data['results'][1]['name'] == 'Dates'
    assert response.data['results'][2]['name'] == 'Apples'
    assert response.data['results'][3]['name'] == 'Coconut'
