from django.test import TestCase
from django.urls import reverse
from accounts.models import CustomUser


class AccountsViewsTests(TestCase):
    def setUp(self):
        self.admin_user = CustomUser.objects.create_user(
            username="testadmin",
            password="password123",
            role="admin",
            is_superuser=True
        )
        self.staff_user = CustomUser.objects.create_user(
            username="teststaff",
            password="password123",
            role="staff",
            is_superuser=False
        )

    def test_login_view_status_code(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_login_view_uses_correct_template(self):
        response = self.client.get(reverse('login'))
        self.assertTemplateUsed(response, 'accounts/login.html')

    def test_admin_login_redirects_to_admin_dashboard(self):
        response = self.client.post(reverse('login'), {
            'username': 'testadmin',
            'password': 'password123'
        })
        self.assertRedirects(response, reverse('admin_dashboard'))

    def test_staff_login_redirects_to_staff_dashboard(self):
        response = self.client.post(reverse('login'), {
            'username': 'teststaff',
            'password': 'password123'
        })
        self.assertRedirects(response, reverse('staff_dashboard'))

    def test_invalid_login_stays_on_page_with_error(self):
        response = self.client.post(reverse('login'), {
            'username': 'wronguser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')
        self.assertContains(response, "Invalid username or password.")

    def test_admin_dashboard_view(self):
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/admin.html')

    def test_staff_dashboard_view(self):
        response = self.client.get(reverse('staff_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/staff.html')

    def test_staff_dashboard_has_real_action_links(self):
        self.client.login(username='teststaff', password='password123')
        response = self.client.get(reverse('staff_dashboard'))

        self.assertContains(response, 'href="/billing/"')
        self.assertContains(response, 'href="/billing/pos_billing/"')
        self.assertContains(response, f'href="/staff/edit/{self.staff_user.id}/"')

    def test_admin_dashboard_has_real_return_link_and_detail_page(self):
        self.client.login(username='testadmin', password='password123')
        dashboard_response = self.client.get(reverse('admin_dashboard'))
        self.assertContains(dashboard_response, 'href="/return-view/"')

        return_response = self.client.get(reverse('return_view'))
        self.assertEqual(return_response.status_code, 200)
        self.assertTemplateUsed(return_response, 'accounts/return_view.html')
