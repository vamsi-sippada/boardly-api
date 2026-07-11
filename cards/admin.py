from django.contrib import admin
from .models import Card, CardMember, Comment, ActivityLog
# Register your models here.

admin.site.register(Card)
admin.site.register(CardMember)
admin.site.register(Comment)
admin.site.register(ActivityLog)