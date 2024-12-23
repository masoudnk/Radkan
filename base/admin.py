from django.apps import apps
from django.contrib import admin
# *************************************** ******************************
from django.contrib.admin.models import LogEntry
from django.db.models import CharField, DateField, DateTimeField, ForeignKey
from django.db.models.fields import TextField, BooleanField
from import_export import resources
from import_export.admin import ImportExportModelAdmin, ImportExportMixin


class LogEntryResource(resources.ModelResource):
    class Meta:
        model = LogEntry
        skip_unchanged = True
        report_skipped = True


class LogEntryAdmin(ImportExportModelAdmin):
    list_display = [field.name for field in LogEntry._meta.fields]
    resource_class = LogEntryResource
    list_filter = ('action_time', 'action_flag', 'user', 'content_type')


admin.site.register(LogEntry, LogEntryAdmin)


# *************************************** ******************************

class ListAdminMixin(ImportExportMixin):
    def __init__(self, model, admin_site):
        filter_list = []
        search_list = []
        filter_horizontal_list = []
        display_list = []
        for field in model._meta.many_to_many:
            filter_horizontal_list.append(field.name)
            for f_field in field.remote_field.model._meta.fields:
                if isinstance(f_field, CharField) or isinstance(f_field, TextField):
                    search_list.append(f'{field.name}__{f_field.name}')
                elif isinstance(f_field, DateField) or isinstance(f_field, DateTimeField) or isinstance(f_field, BooleanField):
                    filter_list.append(f'{field.name}__{f_field.name}')
        self.filter_horizontal = filter_horizontal_list
        for field in model._meta.fields:
            if isinstance(field, TextField):
                search_list.append(field.name)
            else:
                display_list.append(field.name)
            if isinstance(field, CharField):
                search_list.append(field.name)
            elif isinstance(field, DateField) or isinstance(field, DateTimeField) or isinstance(field, BooleanField):
                filter_list.append(field.name)
            elif isinstance(field, ForeignKey):
                for f_field in field.remote_field.model._meta.fields:
                    if isinstance(f_field, CharField) or isinstance(f_field, TextField):
                        search_list.append(f'{field.name}__{f_field.name}')
                    elif isinstance(f_field, DateField) or isinstance(f_field, DateTimeField) or isinstance(f_field,
                                                                                                            BooleanField):
                        filter_list.append(f'{field.name}__{f_field.name}')
        self.list_display = display_list
        self.search_fields = search_list
        self.search_help_text = " , ".join(search_list)
        self.list_filter = filter_list
        # self.actions = [ ]

        super(ListAdminMixin, self).__init__(model, admin_site)


models = apps.get_models()
for model in models:
    admin_class = type('AdminClass', (ListAdminMixin, admin.ModelAdmin), {})
    try:
        admin.site.register(model, admin_class)
    except admin.sites.AlreadyRegistered:
        pass
