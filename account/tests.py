from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from chat.models import Setting
from django.test.utils import override_settings

class RegistrationViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.good_user_payload = {'username': 'mimir', 'email': 'test@nbis.se', 'password1': 'mipasstest', 'password2': 'mipasstest'}
        self.not_nbis_user_payload = {'username': 'mimir', 'email': 'test@ebi.de', 'password1': 'mipasstest', 'password2': 'mipasstest'}
        open_reg_setting = Setting.objects.get(name='open_registration')
        open_reg_setting.value = 'True'
        open_reg_setting.save()

    def test_registration_open(self):
        response = self.client.post(reverse('rest_register'), self.good_user_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_registration_closed(self):
        open_reg_setting = Setting.objects.get(name='open_registration')
        open_reg_setting.value = 'False'
        open_reg_setting.save()
        response = self.client.post(reverse('rest_register'),self.good_user_payload )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {'detail': 'Registration is not yet open.'})

    def test_invalid_email_domain(self):
        response = self.client.post(reverse('rest_register'), self.not_nbis_user_payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {'detail': 'Your email domain is not allowed.'})

    def test_valid_email_domain(self):
        response = self.client.post(reverse('rest_register'), self.good_user_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @override_settings(ACCOUNT_EMAIL_VERIFICATION='optional')
    def test_email_verification_not_required(self):
        response = self.client.post(reverse('rest_register'), self.good_user_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email_verification_required'], 'optional')
        login_response = self.client.post(reverse('rest_login'), {'username': self.good_user_payload['username'],
                                                                  'password': self.good_user_payload['password1']})
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

    @override_settings(ACCOUNT_EMAIL_VERIFICATION='mandatory')
    def test_email_verification_required(self):
        response = self.client.post(reverse('rest_register'), self.good_user_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email_verification_required'], 'mandatory')
        login_response = self.client.post(reverse('rest_login'), {'username': self.good_user_payload['username'],
                                                                  'password': self.good_user_payload['password1']})
        self.assertEqual(login_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_already_registered(self):
        response = self.client.post(reverse('rest_register'), self.good_user_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.post(reverse('rest_register'), self.good_user_payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

