
from django.contrib import admin
from .models import VerificationCategory, VerificationTask, VerificationSubcategory, VerificationSet

admin.site.register(VerificationCategory)
admin.site.register(VerificationSet)
admin.site.register(VerificationSubcategory)

@admin.register(VerificationTask)
class VerificationTaskAdmin(admin.ModelAdmin):
    list_filter = ("category", "expected_result")
    search_fields = ("id", "name",)
