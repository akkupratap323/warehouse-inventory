from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

class ProdMast(models.Model):
    CATEGORY_CHOICES = [
        ('electronics', 'Electronics'),
        ('clothing', 'Clothing'),
        ('food', 'Food'),
        ('books', 'Books'),
        ('other', 'Other'),
    ]
    
    prod_code = models.CharField(max_length=20, unique=True, help_text="Unique product code")
    prod_name = models.CharField(max_length=255, help_text="Product name")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    unit_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Price per unit"
    )
    min_stock_level = models.IntegerField(
        default=0, 
        validators=[MinValueValidator(0)],
        help_text="Minimum stock level alert"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'prodmast'
        verbose_name = 'Product Master'
        verbose_name_plural = 'Product Masters'
    
    def __str__(self):
        return f"{self.prod_code} - {self.prod_name}"

class StckMain(models.Model):
    TRANSACTION_TYPES = [
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
        ('ADJ', 'Adjustment'),
    ]
    
    trans_id = models.AutoField(primary_key=True)
    trans_date = models.DateTimeField(help_text="Transaction date and time")
    trans_type = models.CharField(max_length=3, choices=TRANSACTION_TYPES)
    reference_no = models.CharField(max_length=50, blank=True, help_text="Reference number (PO, Invoice, etc.)")
    remarks = models.TextField(blank=True, help_text="Additional remarks")
    created_by = models.CharField(max_length=50, default='system')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'stckmain'
        verbose_name = 'Stock Transaction'
        verbose_name_plural = 'Stock Transactions'
        ordering = ['-trans_date']
    
    def __str__(self):
        return f"Trans #{self.trans_id} - {self.get_trans_type_display()}"

class StckDetail(models.Model):
    detail_id = models.AutoField(primary_key=True)
    trans = models.ForeignKey(StckMain, on_delete=models.CASCADE, related_name='details')
    product = models.ForeignKey(ProdMast, on_delete=models.CASCADE)
    quantity = models.IntegerField(validators=[MinValueValidator(1)], help_text="Quantity moved")
    unit_cost = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Cost per unit"
    )
    
    class Meta:
        db_table = 'stckdetail'
        verbose_name = 'Stock Detail'
        verbose_name_plural = 'Stock Details'
        unique_together = ['trans', 'product']
    
    def __str__(self):
        return f"{self.product.prod_code} - Qty: {self.quantity}"
    
    @property
    def total_cost(self):
        return self.quantity * self.unit_cost
