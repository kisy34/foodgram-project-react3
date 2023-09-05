from django.contrib import admin

from .models import Follower, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    search_fields = ('email', 'first_name')
    list_filter = ('email', 'first_name')
    empty_value_display = '-пусто-'


@admin.register(Follower)
class FollowAdmin(admin.ModelAdmin):
    empty_value_display = '-пусто-'
