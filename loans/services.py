"""
Business logic services for the Credit Approval System.

All credit score, EMI, eligibility, and interest rate correction logic
lives here — NOT in views.
"""

from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from customers.models import Customer
from loans.models import Loan


# ==================================================================
# EMI CALCULATION (Compound Interest)
# ==================================================================

def calculate_emi(principal: Decimal, annual_rate: Decimal, tenure_months: int) -> Decimal:
    """
    Calculate EMI using the standard compound interest formula:
    EMI = P * r * (1 + r)^n / ((1 + r)^n - 1)

    Where:
        P = principal (loan amount)
        r = monthly interest rate (annual_rate / 12 / 100)
        n = tenure in months
    """
    if tenure_months <= 0:
        return Decimal('0.00')

    if annual_rate <= 0:
        # Zero interest: simple division
        return (principal / tenure_months).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    monthly_rate = annual_rate / Decimal('1200')  # annual_rate / 12 / 100
    compound_factor = (1 + monthly_rate) ** tenure_months

    emi = principal * monthly_rate * compound_factor / (compound_factor - 1)
    return emi.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


# ==================================================================
# CREDIT SCORE CALCULATION (0–100)
# ==================================================================

def calculate_credit_score(customer: Customer) -> int:
    """
    Calculate credit score (0–100) based on:
    i.   Past loans paid on time
    ii.  Number of loans taken
    iii. Loan activity in the current year
    iv.  Total loan volume approved
    v.   If sum of current loans > approved_limit → score = 0
    """
    all_loans = Loan.objects.filter(customer=customer)

    if not all_loans.exists():
        # No loan history — neutral score
        return 50

    # ── Check: sum of current active loan amounts vs approved limit ──
    active_loans = all_loans.filter(is_active=True)
    total_current_loans = sum(loan.loan_amount for loan in active_loans)

    if total_current_loans > customer.approved_limit:
        return 0

    # ── Component scores ──
    score = 0
    total_loans = all_loans.count()

    # (i) Past loans paid on time — up to 30 points
    total_emis = sum(loan.tenure for loan in all_loans)
    total_on_time = sum(loan.emis_paid_on_time for loan in all_loans)

    if total_emis > 0:
        on_time_ratio = total_on_time / total_emis
        score += int(on_time_ratio * 30)

    # (ii) Number of loans taken — up to 20 points
    if total_loans >= 10:
        score += 10  # Too many loans, lower score for this component
    elif total_loans >= 5:
        score += 15
    else:
        score += 20  # Few loans = responsible borrower

    # (iii) Loan activity in the current year — up to 20 points
    current_year = date.today().year
    current_year_loans = all_loans.filter(start_date__year=current_year).count()

    if current_year_loans == 0:
        score += 20  # No new loans this year
    elif current_year_loans <= 2:
        score += 15
    elif current_year_loans <= 5:
        score += 10
    else:
        score += 5  # Too many loans this year

    # (iv) Total loan volume approved — up to 30 points
    total_volume = sum(loan.loan_amount for loan in all_loans)
    approved_limit = customer.approved_limit

    if approved_limit > 0:
        volume_ratio = float(total_volume / approved_limit)
        if volume_ratio <= 0.3:
            score += 30
        elif volume_ratio <= 0.5:
            score += 25
        elif volume_ratio <= 0.8:
            score += 15
        elif volume_ratio <= 1.0:
            score += 10
        else:
            score += 5

    # Clamp to 0–100
    return max(0, min(100, score))


# ==================================================================
# INTEREST RATE CORRECTION
# ==================================================================

def get_corrected_interest_rate(credit_score: int, requested_rate: Decimal) -> tuple:
    """
    Returns (approval_possible, corrected_interest_rate).

    Rules:
    - credit_score > 50 → approve, any rate is fine
    - 30 < credit_score ≤ 50 → approve only if rate > 12%, else correct to 12
    - 10 < credit_score ≤ 30 → approve only if rate > 16%, else correct to 16
    - credit_score ≤ 10 → reject entirely
    """
    if credit_score > 50:
        return True, requested_rate

    if credit_score > 30:
        min_rate = Decimal('12.00')
        if requested_rate > min_rate:
            return True, requested_rate
        else:
            return True, min_rate

    if credit_score > 10:
        min_rate = Decimal('16.00')
        if requested_rate > min_rate:
            return True, requested_rate
        else:
            return True, min_rate

    # credit_score <= 10
    return False, Decimal('0.00')


# ==================================================================
# LOAN ELIGIBILITY CHECK
# ==================================================================

def check_loan_eligibility(customer: Customer, loan_amount: Decimal,
                           interest_rate: Decimal, tenure: int) -> dict:
    """
    Full eligibility check. Returns a dict with:
    - approval (bool)
    - interest_rate (requested)
    - corrected_interest_rate (may differ from requested)
    - tenure
    - monthly_installment
    """
    credit_score = calculate_credit_score(customer)

    # Check interest rate slab
    can_approve, corrected_rate = get_corrected_interest_rate(credit_score, interest_rate)

    # Check EMI affordability: sum of all current EMIs + new EMI must not exceed 50% salary
    active_loans = Loan.objects.filter(customer=customer, is_active=True)
    current_total_emis = sum(loan.monthly_installment for loan in active_loans)

    new_emi = calculate_emi(loan_amount, corrected_rate, tenure)
    total_emis_after = current_total_emis + new_emi
    half_salary = customer.monthly_salary * Decimal('0.5')

    if total_emis_after > half_salary:
        can_approve = False

    corrected_interest_rate = corrected_rate if corrected_rate != interest_rate else None

    return {
        'customer_id': customer.customer_id,
        'approval': can_approve,
        'interest_rate': interest_rate,
        'corrected_interest_rate': corrected_interest_rate,
        'tenure': tenure,
        'monthly_installment': new_emi if can_approve else Decimal('0.00'),
    }


# ==================================================================
# CUSTOMER REGISTRATION
# ==================================================================

def register_customer(first_name: str, last_name: str, age: int,
                      monthly_income: int, phone_number: str) -> Customer:
    """
    Register a new customer. Approved limit = 36 × monthly_salary,
    rounded to nearest lakh (100,000).
    """
    salary = Decimal(str(monthly_income))
    raw_limit = salary * 36
    # Round to nearest lakh
    approved_limit = (raw_limit / 100000).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * 100000

    customer = Customer.objects.create(
        first_name=first_name,
        last_name=last_name,
        age=age,
        phone_number=str(phone_number),
        monthly_salary=salary,
        approved_limit=approved_limit,
        current_debt=Decimal('0'),
    )
    return customer
