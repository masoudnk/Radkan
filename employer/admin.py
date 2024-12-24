from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import User


class CustomUserCreationForm(UserCreationForm):

    class Meta:
        model = User
        fields = ('email','username',)

class CustomUserChangeForm(UserChangeForm):

    class Meta:
        model = User
        fields = ('email','username',)

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm

    model = User

    list_display = ( 'username', 'is_active',
                    'is_superuser', 'last_login',)
    list_filter = ('is_active','is_staff',  'is_superuser')
    fieldsets = (
        (None, {'fields': ( 'mobile', 'email','username', 'password')}),
        ('Permissions', {'fields': ( 'is_active','is_staff',
         'is_superuser', 'groups', 'user_permissions')}),
        ('Dates', {'fields': ('last_login', )})
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2',  'is_active')}
         ),
    )
    search_fields = ('email',)
    ordering = ('email',)

admin.site.register(User, CustomUserAdmin)