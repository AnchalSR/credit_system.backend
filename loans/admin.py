from django.contrib import admin
from .models import Loan


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('loan_id', 'customer', 'loan_amount', 'tenure',
                    'interest_rate', 'monthly_installment', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('customer__first_name', 'customer__last_name')
