"""
Admin site bindings for rg_instructor_analytics app.
"""

from eventtracking import tracker

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from rg_instructor_analytics import models


class InstructorTabsConfigAdmin(admin.ModelAdmin):
    list_display = ('user',) + tuple(models.InstructorTabsConfig.get_tabs_names())
    fieldsets = (
        (None, {'fields': ('user',)}),
        (_('Tabs'), {
            'fields': tuple(models.InstructorTabsConfig.get_tabs_names()),
            'description': _(
                'Enabling additional tabs requires extra traffic, '
                'and might affect system activity. '
                'It might take a little time before data is updated.'
            )
        }),
    )

    def save_model(self, request, obj, form, change):
        super(InstructorTabsConfigAdmin, self).save_model(request, obj, form, change)
        track_info = {
            'instructor': unicode(obj.user),
            'instructor_id': obj.user.id,
            'admin': unicode(request.user),
            'admin_id': request.user.id,
        }
        track_info.update(dict((f, getattr(obj, f, None)) for f in obj.get_tabs_names()))

        tracker.emit(
            'rg_instructor_analytics.tabs_config.changed',
            track_info
        )


admin.site.register(models.GradeStatistic, admin.ModelAdmin)
admin.site.register(models.LastGradeStatUpdate, admin.ModelAdmin)
admin.site.register(models.InstructorTabsConfig, InstructorTabsConfigAdmin)
