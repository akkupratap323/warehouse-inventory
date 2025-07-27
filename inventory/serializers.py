from rest_framework import serializers
from .models import ProdMast, StckMain, StckDetail
from django.db import transaction
from decimal import Decimal

class ProdMastSerializer(serializers.ModelSerializer):
    current_stock = serializers.SerializerMethodField()
    
    class Meta:
        model = ProdMast
        fields = ['id', 'prod_code', 'prod_name', 'category', 'unit_price', 
                 'min_stock_level', 'current_stock', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_current_stock(self, obj):
        stock_in = sum(
            detail.quantity for detail in StckDetail.objects.filter(
                product=obj, trans__trans_type='IN'
            )
        )
        stock_out = sum(
            detail.quantity for detail in StckDetail.objects.filter(
                product=obj, trans__trans_type='OUT'
            )
        )
        adjustments = sum(
            detail.quantity for detail in StckDetail.objects.filter(
                product=obj, trans__trans_type='ADJ'
            )
        )
        return stock_in - stock_out + adjustments
    
    def validate_prod_code(self, value):
        if not value.strip():
            raise serializers.ValidationError("Product code cannot be empty")
        return value.strip().upper()
    
    def validate_unit_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Unit price must be greater than 0")
        return value

class StckDetailSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.prod_name', read_only=True)
    product_code = serializers.CharField(source='product.prod_code', read_only=True)
    total_cost = serializers.ReadOnlyField()
    
    class Meta:
        model = StckDetail
        fields = ['detail_id', 'product', 'product_name', 'product_code', 
                 'quantity', 'unit_cost', 'total_cost']
    
    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0")
        return value
    
    def validate_unit_cost(self, value):
        if value <= 0:
            raise serializers.ValidationError("Unit cost must be greater than 0")
        return value

class StckMainSerializer(serializers.ModelSerializer):
    details = StckDetailSerializer(many=True)
    total_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = StckMain
        fields = ['trans_id', 'trans_date', 'trans_type', 'reference_no', 
                 'remarks', 'created_by', 'created_at', 'details', 'total_amount']
        read_only_fields = ['created_at']
    
    def get_total_amount(self, obj):
        return sum(detail.total_cost for detail in obj.details.all())
    
    def validate_details(self, value):
        if not value:
            raise serializers.ValidationError("At least one product detail is required")
        
        # Check for duplicate products
        product_ids = [detail['product'].id for detail in value]
        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError("Duplicate products not allowed in same transaction")
        
        return value
    
    @transaction.atomic
    def create(self, validated_data):
        details_data = validated_data.pop('details')
        stock_main = StckMain.objects.create(**validated_data)
        
        for detail_data in details_data:
            StckDetail.objects.create(trans=stock_main, **detail_data)
        
        return stock_main

class InventoryReportSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    prod_code = serializers.CharField()
    prod_name = serializers.CharField()
    category = serializers.CharField()
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    current_stock = serializers.IntegerField()
    min_stock_level = serializers.IntegerField()
    stock_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    is_low_stock = serializers.BooleanField()
