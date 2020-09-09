from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import ugettext_lazy as _


class User(AbstractUser):
    username = None
    email = models.EmailField(_('email address'), unique=True)
    pin = models.CharField(max_length=6, null=True, blank=True)
    # audit data
    modified_by = models.CharField(max_length=100, default="")
    modified_on = models.DateField(auto_now_add=True)
    created_by = models.CharField(max_length=100)
    created_on = models.DateTimeField(auto_now_add=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['password']
