from rest_framework import serializers
from .models import Customer


class CustomerRegistrationSerializer(serializers.Serializer):
    """Serializer for POST /register request."""
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    age = serializers.IntegerField()
    monthly_income = serializers.IntegerField()
    phone_number = serializers.CharField(max_length=20)


class CustomerResponseSerializer(serializers.ModelSerializer):
    """Serializer for POST /register response."""
    name = serializers.SerializerMethodField()
    monthly_income = serializers.DecimalField(
        source='monthly_salary', max_digits=12, decimal_places=2
    )

    class Meta:
        model = Customer
        fields = [
            'customer_id', 'name', 'age', 'monthly_income',
            'approved_limit', 'phone_number'
        ]

    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


