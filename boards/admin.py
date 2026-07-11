from django.contrib import admin
from .models import Board, BoardMember, List
# Register your models here.

admin.site.register(Board)
admin.site.register(BoardMember)
admin.site.register(List)