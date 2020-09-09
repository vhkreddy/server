import uuid
from django.core.mail import send_mail
from django.conf import settings
from django.template import Context
from django.template.loader import render_to_string, get_template


def is_valid_uuid(val):
    try:
        return uuid.UUID(str(val))
    except ValueError:
        return None


def send_html_mail(subject=None, message=None, from_email=settings.EMAIL_HOST_USER, recipient_list=[], fail_silently=False, html_template=None, context=None):
    # context = Context(context)
    # html_message = render_to_string(html_template, context)
    html_message = get_template(html_template).render(context)
    send_mail(subject=subject, message=message, from_email=from_email,
              recipient_list=recipient_list,  fail_silently=fail_silently,  html_message=html_message)
