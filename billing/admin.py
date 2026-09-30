from django.contrib import admin
from .models import Sale, SaleItem, Payment, ReturnTransaction, ReturnItem

@admin.register(ReturnTransaction)
class ReturnTransactionAdmin(admin.ModelAdmin):

    list_display = (
        "return_number",
        "sale",
        "processed_by",
        "refund_amount",
        "refund_method",
        "status",
        "created_at",
    )

    search_fields = (
        "return_number",
        "sale__bill_number",
        "processed_by__username",
    )

    list_filter = (
        "refund_method",
        "status",
        "created_at",
    )


@admin.register(ReturnItem)
class ReturnItemAdmin(admin.ModelAdmin):

    list_display = (
        "return_transaction",
        "sale_item",
        "quantity",
        "refund_amount",
    )

    search_fields = (
        "return_transaction__return_number",
        "sale_item__sale__bill_number",
        "sale_item__product__name",
    )

# Register your models here.
