from django import forms
from .models import Member, Contribution, Loan, Membership, Expense, Repayment, BankAccount, BankTransaction
from django import forms as django_forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.utils.text import slugify


User = get_user_model()


class SignupForm(UserCreationForm):
    group_name = django_forms.CharField(max_length=140, required=True, help_text='Name of your Njangi account')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'group_name')

    def save(self, commit=True):
        user = super().save(commit=commit)
        self._group_name = self.cleaned_data.get('group_name')
        return user


class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ['first_name', 'last_name', 'phone', 'email', 'joined_at']


class ContributionForm(forms.ModelForm):
    class Meta:
        model = Contribution
        fields = ['membership', 'amount', 'date', 'note']


class LoanForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = ['membership', 'principal', 'interest_rate', 'due_date', 'status', 'note']


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['meeting', 'amount', 'description', 'date']


class RepaymentForm(forms.ModelForm):
    class Meta:
        model = Repayment
        fields = ['loan', 'amount', 'date', 'note']


class BankAccountForm(forms.ModelForm):
    class Meta:
        model = BankAccount
        fields = ['name', 'account_number', 'starting_balance']


class BankTransactionForm(forms.ModelForm):
    class Meta:
        model = BankTransaction
        fields = ['account', 'date', 'amount', 'kind', 'category', 'reference', 'note']
