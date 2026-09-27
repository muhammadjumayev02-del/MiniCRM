from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from .forms import LeadForm
from .models import Lead


class LeadTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user('tester', password='test-only-password')
        cls.lead = Lead.objects.create(name='Ali', phone='+998901234567', source='Telegram')

    def setUp(self):
        self.client.force_login(self.user)
        self.api = APIClient()
        self.api.force_authenticate(self.user)
        self.detail = reverse('api-lead-detail', args=[self.lead.pk])

    def test_web_requires_login(self):
        self.client.logout()
        for url in ['/', '/leads/new/', f'/leads/{self.lead.pk}/', f'/leads/{self.lead.pk}/edit/', f'/leads/{self.lead.pk}/delete/', f'/leads/{self.lead.pk}/status/']:
            self.assertEqual(self.client.get(url).status_code, 302)

    def test_login_logout(self):
        self.client.logout()
        self.assertContains(self.client.post('/accounts/login/', {'username': 'tester', 'password': 'wrong'}), 'Please enter a correct')
        response = self.client.post('/accounts/login/', {'username': 'tester', 'password': 'test-only-password'})
        self.assertRedirects(response, '/')
        self.assertEqual(self.client.get('/accounts/logout/').status_code, 405)
        self.assertRedirects(self.client.post('/accounts/logout/'), '/accounts/login/')

    def test_api_requires_authentication_for_all_actions(self):
        client = APIClient()
        for method, url in [('get', '/api/leads/'), ('post', '/api/leads/'), ('get', self.detail), ('put', self.detail), ('patch', self.detail), ('delete', self.detail)]:
            self.assertEqual(getattr(client, method)(url).status_code, 401)

    def test_token_authentication(self):
        client = APIClient()
        self.assertEqual(client.post('/api/auth/token/', {'username': 'tester', 'password': 'wrong'}).status_code, 400)
        result = client.post('/api/auth/token/', {'username': 'tester', 'password': 'test-only-password'})
        self.assertEqual(result.status_code, 200)
        client.credentials(HTTP_AUTHORIZATION='Token ' + result.data['token'])
        self.assertEqual(client.get('/api/leads/').status_code, 200)
        client.credentials(HTTP_AUTHORIZATION='Token invalid')
        self.assertEqual(client.get('/api/leads/').status_code, 401)

    def test_session_api_authentication(self):
        self.assertEqual(self.client.get('/api/leads/').status_code, 200)

    def test_csrf_protects_web_and_session_api(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post('/leads/new/', {'name': 'Ali', 'phone': '123'}).status_code, 403)
        self.assertEqual(client.post('/api/leads/', {'name': 'Ali', 'phone': '123'}).status_code, 403)

    def test_api_crud(self):
        response = self.api.post('/api/leads/', {'name': 'Vali', 'email': 'vali@example.com'}, format='json')
        self.assertEqual(response.status_code, 201)
        url = reverse('api-lead-detail', args=[response.data['id']])
        self.assertEqual(self.api.get(url).data['name'], 'Vali')
        response = self.api.put(url, {'name': 'Valijon', 'phone': '99890', 'status': 'Qualified'}, format='json')
        self.assertEqual(response.status_code, 200)
        response = self.api.patch(url, {'status': 'Won'}, format='json')
        self.assertEqual(response.data['status'], 'Won')
        self.assertEqual(self.api.delete(url).status_code, 204)
        self.assertEqual(self.api.get(url).status_code, 404)

    def test_api_invalid_fields(self):
        for data in [{'name': 'Ali'}, {'name': 'Ali', 'phone': ' ', 'email': ' '}, {'name': '', 'phone': '123'}, {'name': 'Ali', 'email': 'bad'}, {'name': 'Ali', 'phone': '123', 'status': 'Unknown'}, {'name': 'a'*151, 'phone': '123'}, {'name': 'Ali', 'phone': None}]:
            with self.subTest(data=data):
                response = self.api.post('/api/leads/', data, format='json')
                self.assertEqual(response.status_code, 400)
                self.assertTrue(response.data)

    def test_partial_update_preserves_contact_validation(self):
        self.assertEqual(self.api.patch(self.detail, {'phone': ''}, format='json').status_code, 400)
        self.assertEqual(self.api.patch(self.detail, {'email': 'ali@example.com'}, format='json').status_code, 200)
        self.assertEqual(self.api.patch(self.detail, {'phone': ''}, format='json').status_code, 200)
        self.assertEqual(self.api.patch(self.detail, {'email': ''}, format='json').status_code, 400)

    def test_read_only_timestamps(self):
        before = self.lead.created_at
        self.api.patch(self.detail, {'created_at': '2000-01-01T00:00:00Z'}, format='json')
        self.lead.refresh_from_db()
        self.assertEqual(self.lead.created_at, before)

    def test_search_and_filter(self):
        Lead.objects.create(name='Vali', email='vali@example.com', status='Won')
        for search in ['Ali', '99890', 'Telegram']:
            response = self.api.get('/api/leads/', {'search': search, 'status': 'New'})
            self.assertEqual(response.data['count'], 1)
            self.assertEqual(response.data['results'][0]['id'], self.lead.pk)
        self.assertEqual(self.api.get('/api/leads/', {'search': 'vali@example.com'}).data['count'], 1)
        self.assertEqual(self.api.get('/api/leads/', {'status': 'Won'}).data['count'], 1)
        self.assertEqual(self.api.get('/api/leads/', {'status': 'wrong'}).status_code, 400)
        self.assertEqual(self.api.get('/api/leads/', {'search': 'absent'}).data['count'], 0)
        response = self.client.get('/', {'search': 'Telegram', 'status': 'New'})
        self.assertEqual(response.context['page_obj'].paginator.count, 1)
        self.assertContains(self.client.get('/', {'status': 'wrong'}), 'Noto‘g‘ri status')

    def test_pagination(self):
        Lead.objects.bulk_create([Lead(name=f'Lead {i}', phone='123') for i in range(12)])
        first = self.api.get('/api/leads/').data
        second = self.api.get('/api/leads/?page=2').data
        self.assertEqual(first['count'], 13)
        self.assertEqual(len(first['results']), 10)
        self.assertEqual(len(second['results']), 3)
        self.assertTrue(first['next'])
        self.assertFalse(set(x['id'] for x in first['results']) & set(x['id'] for x in second['results']))
        self.assertEqual(self.api.get('/api/leads/?page=999').status_code, 404)
        self.assertEqual(len(self.client.get('/?page=2').context['page_obj']), 3)
        self.assertEqual(self.client.get('/?page=bad').status_code, 200)
        response = self.client.get('/?search=Lead&status=New')
        self.assertContains(response, 'search=Lead&status=New&page=2')

    def test_web_crud_and_status(self):
        response = self.client.post('/leads/new/', {'name': 'Web lead', 'phone': '123', 'status': 'New'})
        lead = Lead.objects.get(name='Web lead')
        self.assertRedirects(response, f'/leads/{lead.pk}/')
        self.assertContains(self.client.get(f'/leads/{lead.pk}/'), 'Web lead')
        self.assertEqual(self.client.get(f'/leads/{lead.pk}/edit/').status_code, 200)
        self.client.post(f'/leads/{lead.pk}/edit/', {'name': 'Updated', 'email': 'web@example.com', 'status': 'Contacted'})
        lead.refresh_from_db()
        self.assertEqual(lead.name, 'Updated')
        self.assertEqual(self.client.get(f'/leads/{lead.pk}/status/').status_code, 405)
        self.assertEqual(self.client.post(f'/leads/{lead.pk}/status/', {'status': 'bad'}).status_code, 400)
        for status in Lead.Status.values:
            self.client.post(f'/leads/{lead.pk}/status/', {'status': status})
            lead.refresh_from_db()
            self.assertEqual(lead.status, status)
        self.assertEqual(self.client.get(f'/leads/{lead.pk}/delete/').status_code, 200)
        self.assertTrue(Lead.objects.filter(pk=lead.pk).exists())
        self.assertRedirects(self.client.post(f'/leads/{lead.pk}/delete/'), '/')
        self.assertFalse(Lead.objects.filter(pk=lead.pk).exists())

    def test_web_validation(self):
        response = self.client.post('/leads/new/', {'name': 'Ali', 'status': 'New'})
        self.assertContains(response, 'Telefon yoki emaildan kamida bittasini kiriting.')
        self.assertFalse(LeadForm({'name': 'Ali', 'email': 'bad', 'status': 'New'}).is_valid())
        self.assertFalse(LeadForm({'name': ' ', 'phone': '123', 'status': 'New'}).is_valid())

    @override_settings(DEBUG=False)
    def test_missing_lead(self):
        for suffix in ['', 'edit/', 'delete/']:
            response = self.client.get('/leads/99999/' + suffix)
            self.assertEqual(response.status_code, 404)
            self.assertContains(response, 'Sahifa yoki lead topilmadi', status_code=404)
        self.assertEqual(self.client.post('/leads/99999/status/', {'status': 'Won'}).status_code, 404)
        for method in ['get', 'patch', 'put', 'delete']:
            response = getattr(self.api, method)('/api/leads/99999/')
            self.assertEqual(response.status_code, 404)
            self.assertIn('detail', response.data)

    def test_model_and_database_validation(self):
        with self.assertRaises(ValidationError):
            Lead(name='Ali', phone=' ').full_clean()
        for fields in [{'name': 'Ali'}, {'name': 'Ali', 'phone': '123', 'status': 'bad'}]:
            with self.assertRaises(IntegrityError), transaction.atomic():
                Lead.objects.create(**fields)

    def test_html_is_escaped(self):
        self.lead.note = '<script>alert(1)</script>'
        self.lead.save()
        response = self.client.get(f'/leads/{self.lead.pk}/')
        self.assertContains(response, '&lt;script&gt;')
        self.assertNotContains(response, '<script>')
