from rest_framework import serializers
from .models import Loan


class CheckEligibilityRequestSerializer(serializers.Serializer):
    """Serializer for POST /check-eligibility request."""
    customer_id = serializers.IntegerField()
    loan_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    tenure = serializers.IntegerField()


class CheckEligibilityResponseSerializer(serializers.Serializer):
    """Serializer for POST /check-eligibility response."""
    customer_id = serializers.IntegerField()
    approval = serializers.BooleanField()
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    corrected_interest_rate = serializers.DecimalField(
        max_digits=5, decimal_places=2, allow_null=True
    )
    tenure = serializers.IntegerField()
    monthly_installment = serializers.DecimalField(max_digits=12, decimal_places=2)


class CreateLoanRequestSerializer(serializers.Serializer):
    """Serializer for POST /create-loan request."""
    customer_id = serializers.IntegerField()
    loan_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    tenure = serializers.IntegerField()


class CreateLoanResponseSerializer(serializers.Serializer):
    """Serializer for POST /create-loan response."""
    loan_id = serializers.IntegerField(allow_null=True)
    customer_id = serializers.IntegerField()
    loan_approved = serializers.BooleanField()
    message = serializers.CharField(allow_blank=True, required=False)
    monthly_installment = serializers.DecimalField(
        max_digits=12, decimal_places=2, allow_null=True
    )


class ViewLoanSerializer(serializers.Serializer):
    """Serializer for GET /view-loan/<loan_id> response."""
    loan_id = serializers.IntegerField()
    customer = serializers.DictField()
    loan_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    monthly_installment = serializers.DecimalField(max_digits=12, decimal_places=2)
    tenure = serializers.IntegerField()


class ViewLoansListSerializer(serializers.Serializer):
    """Serializer for each loan in GET /view-loans/<customer_id> response."""
    loan_id = serializers.IntegerField()
    loan_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    monthly_installment = serializers.DecimalField(max_digits=12, decimal_places=2)
    repayments_left = serializers.IntegerField()
