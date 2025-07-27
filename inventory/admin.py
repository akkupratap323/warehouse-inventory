from django.contrib import admin
from .models import ProdMast, StckMain, StckDetail

@admin.register(ProdMast)
class ProdMastAdmin(admin.ModelAdmin):
    list_display = ['prod_code', 'prod_name', 'category', 'unit_price', 'min_stock_level']
    list_filter = ['category', 'created_at']
    search_fields = ['prod_code', 'prod_name']
    ordering = ['prod_code']

class StckDetailInline(admin.TabularInline):
    model = StckDetail
    extra = 1

@admin.register(StckMain)
class StckMainAdmin(admin.ModelAdmin):
    list_display = ['trans_id', 'trans_date', 'trans_type', 'reference_no', 'created_by']
    list_filter = ['trans_type', 'trans_date']
    inlines = [StckDetailInline]
    ordering = ['-trans_date']
