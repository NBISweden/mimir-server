from rest_framework.response import Response
from rest_framework import status
from dj_rest_auth.registration.views import RegisterView
from chat.models import Setting
from allauth.account import app_settings as allauth_account_settings
import re


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

        user = self.perform_create(serializer)
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

    def is_valid_email_domain(self, email, domain_pattern=r'@nbis\.se$'):
        return re.search(domain_pattern, email)
