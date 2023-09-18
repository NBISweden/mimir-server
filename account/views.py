from rest_framework.response import Response
from rest_framework import status
from dj_rest_auth.registration.views import RegisterView
from chat.models import Setting
from allauth.account import app_settings as allauth_account_settings
import re
from smtplib import SMTPRecipientsRefused
from django.contrib.auth import get_user_model

class RegistrationView(RegisterView):
    def create(self, request, *args, **kwargs):
        try:
            open_registration = Setting.objects.get(name='open_registration').value == 'True'
        except Setting.DoesNotExist:
            open_registration = True

        if open_registration is False:
            return Response({'detail': 'Registration is not yet open.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get('email', '')
        if not self.is_valid_email_domain(email):
            return Response({'detail': 'Your email domain is not allowed.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            user = self.perform_create(serializer)
        except SMTPRecipientsRefused:
            return self.remove_unverified_user(email)

        headers = self.get_success_headers(serializer.data)
        data = self.get_response_data(user)

        data['email_verification_required'] = allauth_account_settings.EMAIL_VERIFICATION

        if data:
            response = Response(
                data,
                status=status.HTTP_201_CREATED,
                headers=headers,
            )
        else:
            response = Response(status=status.HTTP_204_NO_CONTENT, headers=headers)

        return response

    @staticmethod
    def is_valid_email_domain(email, domain_pattern=r'@nbis\.se$'):
        return re.search(domain_pattern, email)

    @staticmethod
    def remove_unverified_user(email):
        user_model = get_user_model()
        try:
            user_to_delete = user_model.objects.get(email=email)
            user_to_delete.delete()
            return Response({'detail': 'Email could not be sent'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except user_model.DoesNotExist:
                return Response({'detail': 'Internal server error.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
