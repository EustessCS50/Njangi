from rest_framework import serializers
from .. import models

class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Member
        fields = '__all__'

class MembershipSerializer(serializers.ModelSerializer):
    member = MemberSerializer(read_only=True)
    class Meta:
        model = models.Membership
        fields = '__all__'

class MeetingSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Meeting
        fields = '__all__'

class ContributionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Contribution
        fields = '__all__'

class LoanSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Loan
        fields = '__all__'

class RepaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Repayment
        fields = '__all__'

class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Expense
        fields = '__all__'

class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BankAccount
        fields = '__all__'

class BankTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BankTransaction
        fields = '__all__'


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Group
        fields = '__all__'
