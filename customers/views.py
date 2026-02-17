"""
API views for customer registration.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import CustomerRegistrationSerializer, CustomerResponseSerializer
from loans.services import register_customer


class RegisterCustomerView(APIView):
    """POST /register — Register a new customer."""

    def post(self, request):
        serializer = CustomerRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            customer = register_customer(
                first_name=data['first_name'],
                last_name=data['last_name'],
                age=data['age'],
                monthly_income=data['monthly_income'],
                phone_number=data['phone_number'],
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        response_serializer = CustomerResponseSerializer(customer)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
