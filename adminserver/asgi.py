import os
from channels.routing import get_default_application
# import django
# from channels.asgi import get_channel_layer

# django.setup()
# application = get_default_application()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "adminserver.settings")
channel_layer = get_channel_layer()

