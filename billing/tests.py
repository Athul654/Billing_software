from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from products.models import Product
from .models import ReturnItem, ReturnTransaction, Sale, SaleItem


class BillingHomePageTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='cashier1',
            password='testpass123',
            first_name='Cashier',
            last_name='One',
            role='staff',
            is_active=True,
        )
        self.product = Product.objects.create(
            name='Cotton Shirt',
            sku='SKU-001',
            purchase_price=Decimal('250.00'),
            selling_price=Decimal('450.00'),
            stock_quantity=20,
            is_active=True,
        )
        self.sale = Sale.objects.create(
            bill_number='INV-1001',
            staff=self.user,
            subtotal=Decimal('450.00'),
            discount=Decimal('0.00'),
            total_amount=Decimal('450.00'),
            payment_method='cash',
            status='completed',
        )
        SaleItem.objects.create(
            sale=self.sale,
            product=self.product,
            quantity=1,
            unit_price=Decimal('450.00'),
            total_price=Decimal('450.00'),
        )

    def test_billing_home_route_loads_real_database_data(self):
        self.client.login(username='cashier1', password='testpass123')
        response = self.client.get(reverse('billing_home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cotton Shirt')
        self.assertContains(response, 'INV-1001')
        self.assertContains(response, '450.00')

    def test_pos_billing_reduces_stock_when_sale_is_created(self):
        self.client.login(username='cashier1', password='testpass123')
        self.product.stock_quantity = 10
        self.product.save()

        response = self.client.post(reverse('pos_billing'), {
            'qty_%s' % self.product.id: '2',
            'payment_method': 'cash',
            'discount': '0',
        })

        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 8)
        self.assertTrue(Sale.objects.filter(bill_number__startswith='INV-').exists())

    def test_returns_page_loads_real_sale_data(self):
        self.client.login(username='cashier1', password='testpass123')

        response = self.client.get(reverse('returns'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'INV-1001')
        self.assertContains(response, 'Cotton Shirt')

    def test_return_process_restores_stock_and_creates_transaction(self):
        self.client.login(username='cashier1', password='testpass123')
        self.product.stock_quantity = 5
        self.product.save()

        response = self.client.post(reverse('returns'), {
            'sale_id': str(self.sale.id),
            'return_selected': str(self.product.id),
            'return_qty_{}'.format(self.product.id): '1',
            'refund_method': 'cash',
            'reason': 'Customer changed mind',
        })

        self.assertEqual(response.status_code, 200)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 6)
        self.assertTrue(ReturnTransaction.objects.filter(sale=self.sale).exists())
        self.assertTrue(ReturnItem.objects.filter(sale_item__product=self.product).exists())
