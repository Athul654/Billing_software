from django.test import TestCase
from django.urls import reverse


class ProductPageNavigationTests(TestCase):
    def test_products_page_links_to_staff_page(self):
        response = self.client.get(reverse('products'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="/staff/"')
