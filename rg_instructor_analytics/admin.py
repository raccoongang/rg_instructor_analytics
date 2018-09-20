"""
Admin site bindings for rg_instructor_analytics app.
"""

from django.contrib import admin

from rg_instructor_analytics import models

admin.site.register(models.EnrollmentTabCache, admin.ModelAdmin)
admin.site.register(models.EnrollmentByStudent, admin.ModelAdmin)
admin.site.register(models.GradeStatistic, admin.ModelAdmin)
admin.site.register(models.LastGradeStatUpdate, admin.ModelAdmin)
