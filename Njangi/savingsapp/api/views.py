from rest_framework import viewsets, permissions
from django.shortcuts import render
from .. import models
from .serializers import (
    MemberSerializer, MembershipSerializer, ContributionSerializer, LoanSerializer,
    RepaymentSerializer, ExpenseSerializer, BankAccountSerializer, BankTransactionSerializer, MeetingSerializer
)

class IsAuthenticatedOrReadOnly(permissions.IsAuthenticated):
    pass

class MemberViewSet(viewsets.ModelViewSet):
    queryset = models.Member.objects.all().order_by('first_name')
    serializer_class = MemberSerializer

class MembershipViewSet(viewsets.ModelViewSet):
    queryset = models.Membership.objects.all()
    serializer_class = MembershipSerializer

class MeetingsViewSet(viewsets.ModelViewSet):
    queryset = models.Meeting.objects.all()
    serializer_class = MeetingSerializer

class ContributionViewSet(viewsets.ModelViewSet):
    queryset = models.Contribution.objects.select_related('membership__member', 'membership__meeting').all().order_by('-date')
    serializer_class = ContributionSerializer

class LoanViewSet(viewsets.ModelViewSet):
    queryset = models.Loan.objects.select_related('membership__member').all().order_by('-created_at')
    serializer_class = LoanSerializer

class RepaymentViewSet(viewsets.ModelViewSet):
    queryset = models.Repayment.objects.select_related('loan').all().order_by('-date')
    serializer_class = RepaymentSerializer

class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = models.Expense.objects.select_related('meeting').all().order_by('-date')
    serializer_class = ExpenseSerializer

class BankAccountViewSet(viewsets.ModelViewSet):
    queryset = models.BankAccount.objects.all().order_by('name')
    serializer_class = BankAccountSerializer

class BankTransactionViewSet(viewsets.ModelViewSet):
    queryset = models.BankTransaction.objects.select_related('account').all().order_by('-date')
    serializer_class = BankTransactionSerializer


def api_help(request):
    """Render a simple API help / documentation page."""
    return render(request, 'savingsapp/api_help.html')


class GroupViewSet(viewsets.ModelViewSet):
    queryset = models.Group.objects.all().order_by('name')
    # import serializer lazily to avoid circular imports if needed
    from .serializers import GroupSerializer
    serializer_class = GroupSerializer
