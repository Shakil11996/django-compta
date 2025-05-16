from django.contrib import admin
from .models import Account, Operation

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'label', 'description')

class OperationAdmin(admin.ModelAdmin):
    readonly_fields = ['gross_amount', 'vat_amount', 'input_date', 'id']

admin.site.register(Operation, OperationAdmin)
