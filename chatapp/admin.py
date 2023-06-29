from django.contrib import admin
from chatapp.models import User, Message


admin.site.register(User)
admin.site.register(Message)