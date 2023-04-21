from django.urls import path, include
from rest_framework import routers
from rest_framework.authtoken.views import obtain_auth_token
from shopping_list.api.views import (
    ListAddShoppingList,
    ShoppingListDetail,
    ListAddShoppingItem,
    ShoppingItemDetail,
    ShoppingListAddMembers,
    ShoppingListRemoveMembers,
    SearchShoppingItems,
)


urlpatterns = [
    path('api-auth', include('rest_framework.urls', namespace='rest_framework')),
    path('api-token-auth/', obtain_auth_token, name='api-token-auth'),
    path('api/search-shopping-items/', SearchShoppingItems.as_view(), name='search-shopping-items'),
    path('api/shopping-lists/', ListAddShoppingList.as_view(), name='all-shopping-lists'),
    path(
        'api/shopping-lists/<uuid:pk>/', ShoppingListDetail.as_view(), name='shopping-list-detail'
    ),
    path(
        'api/shopping-lists/<uuid:pk>/add-members/',
        ShoppingListAddMembers.as_view(),
        name='shopping-list-add-members',
    ),
    path(
        'api/shopping-lists/<uuid:pk>/remove-members/',
        ShoppingListRemoveMembers.as_view(),
        name='shopping-list-remove-members',
    ),
    path(
        'api/shopping-lists/<uuid:pk>/shopping-items/',
        ListAddShoppingItem.as_view(),
        name='list-add-shopping-item',
    ),
    path(
        'api/shopping-lists/<uuid:pk>/shopping-items/<uuid:item_pk>/',
        ShoppingItemDetail.as_view(),
        name='shopping-item-detail',
    ),
]
