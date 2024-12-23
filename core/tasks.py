from allauth.socialaccount.providers.mediawiki.provider import settings
from celery import shared_task
from django.core.mail.message import EmailMultiAlternatives


@shared_task
def send_email(subject, message, recipient_list, **kwargs):
    try:
        msg = EmailMultiAlternatives(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
        msg.content_subtype = "html"
        msg.send()
    except Exception as e:
        print(e)
