from django.db import models

# Create your models here.


from django.conf import settings
from products.models import Product


class Sale(models.Model):
    PAYMENT_METHODS = (
        ("cash", "Cash"),
        ("upi", "UPI"),
        ("card", "Card"),
    )

    STATUS_CHOICES = (
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    )

    bill_number = models.CharField(
        max_length=50,
        unique=True
    )

    staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sales"
    )

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="completed"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.bill_number


class SaleItem(models.Model):
    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name="items"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="sale_items"
    )

    quantity = models.PositiveIntegerField()

    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    def __str__(self):
        return f"{self.sale.bill_number} - {self.product.name}"


class Payment(models.Model):
    sale = models.OneToOneField(
        Sale,
        on_delete=models.CASCADE,
        related_name="payment"
    )

    payment_method = models.CharField(
        max_length=20,
        choices=Sale.PAYMENT_METHODS
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.sale.bill_number} - {self.amount}"

class ReturnTransaction(models.Model):

    REFUND_METHODS = (
        ("cash", "Cash"),
        ("upi", "UPI"),
        ("card", "Card"),
    )

    STATUS_CHOICES = (
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    )

    return_number = models.CharField(
        max_length=50,
        unique=True
    )

    sale = models.ForeignKey(
        Sale,
        on_delete=models.PROTECT,
        related_name="returns"
    )

    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="processed_returns"
    )

    refund_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    refund_method = models.CharField(
        max_length=20,
        choices=REFUND_METHODS
    )

    reason = models.CharField(
        max_length=255,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="completed"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.return_number


class ReturnItem(models.Model):

    return_transaction = models.ForeignKey(
        ReturnTransaction,
        on_delete=models.CASCADE,
        related_name="items"
    )

    sale_item = models.ForeignKey(
        SaleItem,
        on_delete=models.PROTECT,
        related_name="return_items"
    )

    quantity = models.PositiveIntegerField()

    refund_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    def __str__(self):
        return (
            f"{self.return_transaction.return_number} - "
            f"{self.sale_item.product.name}"
        )