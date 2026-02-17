"""
API views for loan operations.
"""

from decimal import Decimal
from datetime import date
from dateutil.relativedelta import relativedelta

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from customers.models import Customer
from .models import Loan
from .serializers import (
    CheckEligibilityRequestSerializer,
    CheckEligibilityResponseSerializer,
    CreateLoanRequestSerializer,
    CreateLoanResponseSerializer,
    ViewLoanSerializer,
    ViewLoansListSerializer,
)
from .services import check_loan_eligibility


class CheckEligibilityView(APIView):
    """POST /check-eligibility — Check loan eligibility for a customer."""

    def post(self, request):
        serializer = CheckEligibilityRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            customer = Customer.objects.get(customer_id=data['customer_id'])
        except Customer.DoesNotExist:
            return Response(
                {'error': f"Customer with ID {data['customer_id']} not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        result = check_loan_eligibility(
            customer=customer,
            loan_amount=data['loan_amount'],
            interest_rate=data['interest_rate'],
            tenure=data['tenure'],
        )

        response_serializer = CheckEligibilityResponseSerializer(result)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class CreateLoanView(APIView):
    """POST /create-loan — Create a new loan if eligible."""

    def post(self, request):
        serializer = CreateLoanRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            customer = Customer.objects.get(customer_id=data['customer_id'])
        except Customer.DoesNotExist:
            return Response(
                {'error': f"Customer with ID {data['customer_id']} not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Run eligibility check
        eligibility = check_loan_eligibility(
            customer=customer,
            loan_amount=data['loan_amount'],
            interest_rate=data['interest_rate'],
            tenure=data['tenure'],
        )

        if not eligibility['approval']:
            response_data = {
                'loan_id': None,
                'customer_id': customer.customer_id,
                'loan_approved': False,
                'message': 'Loan not approved based on eligibility criteria.',
                'monthly_installment': None,
            }
            return Response(response_data, status=status.HTTP_200_OK)

        # Use corrected interest rate if applicable
        final_rate = eligibility.get('corrected_interest_rate') or data['interest_rate']
        emi = eligibility['monthly_installment']
        today = date.today()

        loan = Loan.objects.create(
            customer=customer,
            loan_amount=data['loan_amount'],
            tenure=data['tenure'],
            interest_rate=final_rate,
            monthly_installment=emi,
            emis_paid_on_time=0,
            start_date=today,
            end_date=today + relativedelta(months=data['tenure']),
            is_active=True,
        )

        # Update customer's current debt
        customer.current_debt += data['loan_amount']
        customer.save(update_fields=['current_debt'])

        response_data = {
            'loan_id': loan.loan_id,
            'customer_id': customer.customer_id,
            'loan_approved': True,
            'message': 'Loan approved successfully.',
            'monthly_installment': emi,
        }
        return Response(response_data, status=status.HTTP_201_CREATED)


class ViewLoanView(APIView):
    """GET /view-loan/<loan_id> — View details of a single loan."""

    def get(self, request, loan_id):
        try:
            loan = Loan.objects.select_related('customer').get(loan_id=loan_id)
        except Loan.DoesNotExist:
            return Response(
                {'error': f"Loan with ID {loan_id} not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        customer = loan.customer
        response_data = {
            'loan_id': loan.loan_id,
            'customer': {
                'id': customer.customer_id,
                'first_name': customer.first_name,
                'last_name': customer.last_name,
                'phone_number': customer.phone_number,
                'age': customer.age,
            },
            'loan_amount': loan.loan_amount,
            'interest_rate': loan.interest_rate,
            'monthly_installment': loan.monthly_installment,
            'tenure': loan.tenure,
        }

        serializer = ViewLoanSerializer(response_data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ViewLoansView(APIView):
    """GET /view-loans/<customer_id> — View all loans of a customer."""

    def get(self, request, customer_id):
        try:
            customer = Customer.objects.get(customer_id=customer_id)
        except Customer.DoesNotExist:
            return Response(
                {'error': f"Customer with ID {customer_id} not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        active_loans = Loan.objects.filter(customer=customer, is_active=True)
        loans_data = []

        for loan in active_loans:
            repayments_left = loan.tenure - loan.emis_paid_on_time
            if repayments_left < 0:
                repayments_left = 0

            loans_data.append({
                'loan_id': loan.loan_id,
                'loan_amount': loan.loan_amount,
                'interest_rate': loan.interest_rate,
                'monthly_installment': loan.monthly_installment,
                'repayments_left': repayments_left,
            })

        serializer = ViewLoansListSerializer(loans_data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
