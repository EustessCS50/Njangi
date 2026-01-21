from django.db import models
from django.utils import timezone
from django.conf import settings
from decimal import Decimal


class Meeting(models.Model):
	"""Represents a Njangi meeting/yearly cycle (e.g., 2025 Njangi)."""

	# Optional tenancy: a Meeting can belong to a Group (Njangi account) in the SaaS model
	group = models.ForeignKey('Group', on_delete=models.CASCADE, null=True, blank=True, related_name='meetings')
	name = models.CharField(max_length=120)
	year = models.PositiveIntegerField()
	start_date = models.DateField(default=timezone.now)
	end_date = models.DateField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = (('name', 'year'),)

	def __str__(self):
		return f"{self.name} {self.year}"


class Member(models.Model):
	"""A person participating in one or more meetings."""
	# Members are scoped to a Group when using SaaS multi-tenant setup.
	group = models.ForeignKey('Group', on_delete=models.CASCADE, null=True, blank=True, related_name='members')
	first_name = models.CharField(max_length=80)
	last_name = models.CharField(max_length=80, blank=True)
	phone = models.CharField(max_length=30, blank=True)
	email = models.EmailField(blank=True)
	joined_at = models.DateField(default=timezone.now)

	def __str__(self):
		return f"{self.first_name} {self.last_name}".strip()


class Membership(models.Model):
	"""Links `Member` to a `Meeting` and stores member-specific settings for that meeting."""
	member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='memberships')
	meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='memberships')
	monthly_due = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	is_active = models.BooleanField(default=True)

	class Meta:
		unique_together = (('member', 'meeting'),)

	def __str__(self):
		return f"{self.member} @ {self.meeting}"

	def total_contributions(self):
		total = self.contributions.aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
		return Decimal(total)

	def balance(self):
		return self.total_contributions()


class Contribution(models.Model):
	"""Savings/contribution record for a member in a meeting."""
	membership = models.ForeignKey(Membership, on_delete=models.CASCADE, related_name='contributions')
	amount = models.DecimalField(max_digits=12, decimal_places=2)
	date = models.DateField(default=timezone.now)
	note = models.CharField(max_length=255, blank=True)

	def __str__(self):
		return f"{self.membership.member}: {self.amount} on {self.date}"


class Loan(models.Model):
	"""Loan issued to a membership during a meeting."""
	STATUS_CHOICES = (
		('pending', 'Pending'),
		('approved', 'Approved'),
		('rejected', 'Rejected'),
		('paid', 'Paid'),
	)

	membership = models.ForeignKey(Membership, on_delete=models.CASCADE, related_name='loans')
	principal = models.DecimalField(max_digits=12, decimal_places=2)
	interest_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text='Percent per annum or per agreed period')
	created_at = models.DateTimeField(auto_now_add=True)
	approved_at = models.DateTimeField(null=True, blank=True)
	due_date = models.DateField(null=True, blank=True)
	status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='pending')
	note = models.TextField(blank=True)

	def interest_amount(self):
		# simple interest calculation for display; calling code should specify period if needed
		return (self.principal * self.interest_rate) / 100

	def outstanding(self):
		paid = self.repayments.aggregate(total=models.Sum('amount'))['total'] or 0
		return (self.principal + self.interest_amount()) - paid

	def __str__(self):
		return f"Loan {self.id} for {self.membership.member} ({self.status})"


class Repayment(models.Model):
	loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='repayments')
	amount = models.DecimalField(max_digits=12, decimal_places=2)
	date = models.DateField(default=timezone.now)
	note = models.CharField(max_length=255, blank=True)

	def __str__(self):
		return f"{self.amount} to Loan {self.loan_id} on {self.date}"


class Expense(models.Model):
	"""Operational expense for a meeting (bank fees, transport, etc.)."""
	meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='expenses')
	# optional group link for tenancy clarity
	group = models.ForeignKey('Group', on_delete=models.CASCADE, null=True, blank=True, related_name='expenses')
	amount = models.DecimalField(max_digits=12, decimal_places=2)
	description = models.CharField(max_length=255, blank=True)
	date = models.DateField(default=timezone.now)

	def __str__(self):
		return f"{self.meeting} expense {self.amount} on {self.date}"


class YearEndDistribution(models.Model):
	"""Stores computed year-end distribution per member for a meeting/year."""
	meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='distributions')
	member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='distributions')
	# optional group link for tenancy clarity
	group = models.ForeignKey('Group', on_delete=models.CASCADE, null=True, blank=True, related_name='distributions')
	savings_interest = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	total_returned = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	year = models.PositiveIntegerField()

	class Meta:
		unique_together = (('meeting', 'member', 'year'),)

	def __str__(self):
		return f"Distribution {self.meeting} {self.member} {self.year}"


class BankAccount(models.Model):
	"""Simple bank account tracker. Use `starting_balance` for initial funding; current balance is
	derived on the dashboard by combining contributions, repayments, loan disbursements and expenses.
	"""
	# optional group: bank accounts can be scoped to a Group (Njangi account)
	group = models.ForeignKey('Group', on_delete=models.CASCADE, null=True, blank=True, related_name='bank_accounts')
	name = models.CharField(max_length=140)
	account_number = models.CharField(max_length=64, blank=True)
	starting_balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"{self.name} ({self.account_number})" if self.account_number else self.name


class BankTransaction(models.Model):
	"""A simple transaction ledger for a BankAccount.

	`kind` is either 'credit' (inflow) or 'debit' (outflow). Amount is stored positive; ledger
	interpretation depends on `kind`.
	"""
	KIND_CHOICES = (
		('credit', 'Credit'),
		('debit', 'Debit'),
	)

	account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='transactions')
	date = models.DateField(default=timezone.now)
	amount = models.DecimalField(max_digits=14, decimal_places=2)
	kind = models.CharField(max_length=8, choices=KIND_CHOICES)
	category = models.CharField(max_length=120, blank=True)
	reference = models.CharField(max_length=120, blank=True)
	note = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ('-date', '-created_at')

	def __str__(self):
		return f"{self.get_kind_display()} {self.amount} on {self.date} ({self.account})"

	def signed_amount(self):
		"""Return signed Decimal: positive for credits, negative for debits."""
		amt = Decimal(self.amount)
		return amt if self.kind == 'credit' else (amt * Decimal('-1'))



class Group(models.Model):
	"""A top-level 'Njangi' account — multi-tenant unit for the SaaS model.

	Owners (users) can administer one or more Groups. Members, Meetings and BankAccounts
	can be scoped to a Group. Fields are optional to allow incremental migration.
	"""
	name = models.CharField(max_length=140)
	slug = models.SlugField(max_length=140, unique=True)
	owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_groups')
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.name


# Convenience methods on Member for summaries and eligibility
def _safe_decimal(value):
	return Decimal(value) if value is not None else Decimal('0')


def member_total_savings(self, meeting=None):
	q = self.memberships.all()
	if meeting:
		q = q.filter(meeting=meeting)
	total = 0
	for m in q:
		total += m.contributions.aggregate(total=models.Sum('amount'))['total'] or 0
	return Decimal(total)


def member_outstanding_loans(self, meeting=None):
	loans = Loan.objects.filter(membership__member=self)
	if meeting:
		loans = loans.filter(membership__meeting=meeting)
	total = Decimal('0')
	for loan in loans:
		total += _safe_decimal(loan.outstanding())
	return total


def member_eligibility_suggestion(self, meeting=None):
	"""Simple heuristic: eligibility proportional to savings and repayment history.

	Returns a Decimal suggested maximum loan amount.
	"""
	total_savings = member_total_savings(self, meeting)
	loans = Loan.objects.filter(membership__member=self)
	if meeting:
		loans = loans.filter(membership__meeting=meeting)
	loan_count = loans.count()
	if loan_count == 0:
		timeliness = Decimal('1')
	else:
		paid_count = loans.filter(status='paid').count()
		timeliness = Decimal(paid_count) / Decimal(loan_count)
	# make eligibility = savings * factor * timeliness
	factor = Decimal('1.5')
	return (Decimal(total_savings) * factor * timeliness).quantize(Decimal('0.01'))


def member_statement(self, meeting=None):
	"""Return a concise statement summary (dict) for a member optionally scoped to a meeting."""
	total_savings = member_total_savings(self, meeting)
	outstanding = member_outstanding_loans(self, meeting)
	eligibility = member_eligibility_suggestion(self, meeting)
	return {
		'member': str(self),
		'total_savings': Decimal(total_savings),
		'outstanding_loans': Decimal(outstanding),
		'eligibility_suggestion': eligibility,
	}


# attach helper methods to Member dynamically
Member.total_savings = member_total_savings
Member.outstanding_loans = member_outstanding_loans
Member.eligibility_suggestion = member_eligibility_suggestion
Member.statement = member_statement
