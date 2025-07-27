from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProdMastViewSet, StckMainViewSet, InventoryReportViewSet

router = DefaultRouter()
router.register(r'products', ProdMastViewSet)
router.register(r'transactions', StckMainViewSet)
router.register(r'inventory', InventoryReportViewSet, basename='inventory')

urlpatterns = [
    path('', include(router.urls)),
]
