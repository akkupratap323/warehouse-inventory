from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Case, When, IntegerField, F
from django.db.models.functions import Coalesce
from .models import ProdMast, StckMain, StckDetail
from .serializers import (
    ProdMastSerializer, StckMainSerializer, 
    StckDetailSerializer, InventoryReportSerializer
)

class ProdMastViewSet(viewsets.ModelViewSet):
    queryset = ProdMast.objects.all().order_by('prod_code')
    serializer_class = ProdMastSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.query_params.get('category')
        search = self.request.query_params.get('search')
        
        if category:
            queryset = queryset.filter(category=category)
        
        if search:
            queryset = queryset.filter(
                prod_name__icontains=search
            ) | queryset.filter(
                prod_code__icontains=search
            )
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get products with low stock levels"""
        products = []
        for product in self.get_queryset():
            serializer = self.get_serializer(product)
            data = serializer.data
            if data['current_stock'] <= product.min_stock_level:
                products.append(data)
        
        return Response(products)

class StckMainViewSet(viewsets.ModelViewSet):
    queryset = StckMain.objects.all().prefetch_related('details__product')
    serializer_class = StckMainSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        trans_type = self.request.query_params.get('trans_type')
        
        if trans_type:
            queryset = queryset.filter(trans_type=trans_type)
        
        return queryset

class InventoryReportViewSet(viewsets.ViewSet):
    """
    ViewSet for inventory reports and analytics
    """
    
    def list(self, request):
        """Get current inventory status for all products"""
        products = ProdMast.objects.all()
        report_data = []
        
        for product in products:
            # Calculate current stock
            stock_in = StckDetail.objects.filter(
                product=product, trans__trans_type='IN'
            ).aggregate(total=Coalesce(Sum('quantity'), 0))['total']
            
            stock_out = StckDetail.objects.filter(
                product=product, trans__trans_type='OUT'
            ).aggregate(total=Coalesce(Sum('quantity'), 0))['total']
            
            adjustments = StckDetail.objects.filter(
                product=product, trans__trans_type='ADJ'
            ).aggregate(total=Coalesce(Sum('quantity'), 0))['total']
            
            current_stock = stock_in - stock_out + adjustments
            stock_value = current_stock * product.unit_price
            
            report_data.append({
                'product_id': product.id,
                'prod_code': product.prod_code,
                'prod_name': product.prod_name,
                'category': product.category,
                'unit_price': product.unit_price,
                'current_stock': current_stock,
                'min_stock_level': product.min_stock_level,
                'stock_value': stock_value,
                'is_low_stock': current_stock <= product.min_stock_level
            })
        
        serializer = InventoryReportSerializer(report_data, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get inventory summary statistics"""
        total_products = ProdMast.objects.count()
        
        # Calculate total stock value and low stock items
        products = ProdMast.objects.all()
        total_value = 0
        low_stock_count = 0
        
        for product in products:
            stock_in = StckDetail.objects.filter(
                product=product, trans__trans_type='IN'
            ).aggregate(total=Coalesce(Sum('quantity'), 0))['total']
            
            stock_out = StckDetail.objects.filter(
                product=product, trans__trans_type='OUT'
            ).aggregate(total=Coalesce(Sum('quantity'), 0))['total']
            
            adjustments = StckDetail.objects.filter(
                product=product, trans__trans_type='ADJ'
            ).aggregate(total=Coalesce(Sum('quantity'), 0))['total']
            
            current_stock = stock_in - stock_out + adjustments
            total_value += current_stock * product.unit_price
            
            if current_stock <= product.min_stock_level:
                low_stock_count += 1
        
        return Response({
            'total_products': total_products,
            'total_stock_value': total_value,
            'low_stock_items': low_stock_count,
            'total_transactions': StckMain.objects.count()
        })
