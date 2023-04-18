from django.urls import path, include
from rest_framework import routers

from shopping_list.api.viewsets import ShoppingItemViewSet
from shopping_list.api.views import (
    ListAddShoppingList,
    ShoppingListDetail,
    AddShoppingItem,
    ShoppingItemDetail,
)

router = routers.DefaultRouter()
router.register('shopping-items', ShoppingItemViewSet, basename='shopping-items')

urlpatterns = [
    # path('api/', include(router.urls)),
    path('api/shopping-lists/', ListAddShoppingList.as_view(), name='all_shopping_lists'),
    path(
        'api/shopping-lists/<uuid:pk>/', ShoppingListDetail.as_view(), name='shopping_list_detail'
    ),
    path(
        'api/shopping-lists/<uuid:pk>/shopping-items/',
        AddShoppingItem.as_view(),
        name='add-shopping-item',
    ),
    path(
        'api/shopping-lists/<uuid:pk>/shopping-items/<uuid:item_pk>/',
        ShoppingItemDetail.as_view(),
        name='shopping-item-detail',
    ),
]
