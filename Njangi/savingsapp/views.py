from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.db.models import Sum, Q
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from . import models
from .utils import exporters
from .forms import MemberForm, ContributionForm, LoanForm, ExpenseForm, RepaymentForm
from .forms import BankAccountForm, BankTransactionForm
from .forms import SignupForm
from django.utils.text import slugify
import csv
import io
from decimal import Decimal


@login_required(login_url="login")
def dashboard(request):
	# If user is authenticated and owns a Group, scope dashboard to that Group
	group = None
	if request.user.is_authenticated:
		try:
			group = request.user.owned_groups.first()
		except Exception:
			group = None

	if group:
		total_members = models.Member.objects.filter(group=group).count()
		total_contributions = models.Contribution.objects.filter(membership__meeting__group=group).aggregate(total=Sum('amount'))['total'] or 0
		total_loans = models.Loan.objects.filter(membership__meeting__group=group).aggregate(total=Sum('principal'))['total'] or 0
	else:
		total_members = models.Member.objects.count()
		total_contributions = models.Contribution.objects.aggregate(total=Sum('amount'))['total'] or 0
		total_loans = models.Loan.objects.aggregate(total=Sum('principal'))['total'] or 0
	outstanding = 0
	loans_iter = models.Loan.objects.all() if not group else models.Loan.objects.filter(membership__meeting__group=group)
	for loan in loans_iter:
		try:
			outstanding += loan.outstanding()
		except Exception:
			pass

	# Bank balance calculation: starting balances + contributions + repayments - disbursed loans - expenses
	BankAccount = getattr(models, 'BankAccount', None)
	BankTransaction = getattr(models, 'BankTransaction', None)
	if BankTransaction is not None:
		# calculate bank balance from transactions + starting balances for safety
		if group:
			accounts = BankAccount.objects.filter(group=group)
			txns = BankTransaction.objects.filter(account__in=accounts)
		else:
			txns = BankTransaction.objects.all()
		txn_total = txns.aggregate(total=Sum('amount'))['total'] or Decimal('0')
		# signed total: credits count positive, debits negative
		# easier: sum signed_amount for each transaction
		signed = Decimal('0')
		for t in txns:
			try:
				signed += t.signed_amount()
			except Exception:
				continue
		starting = (accounts.aggregate(total=Sum('starting_balance'))['total'] if BankAccount is not None and group else BankAccount.objects.aggregate(total=Sum('starting_balance'))['total']) if BankAccount is not None else Decimal('0')
		starting = Decimal(starting or 0)
		bank_balance = starting + signed
	else:
		if group:
			starting = BankAccount.objects.filter(group=group).aggregate(total=Sum('starting_balance'))['total'] or Decimal('0')
			contribs = models.Contribution.objects.filter(membership__meeting__group=group).aggregate(total=Sum('amount'))['total'] or Decimal('0')
			repayments = models.Repayment.objects.filter(loan__membership__meeting__group=group).aggregate(total=Sum('amount'))['total'] or Decimal('0')
			loan_disbursed = models.Loan.objects.filter(membership__meeting__group=group, status='approved').aggregate(total=Sum('principal'))['total'] or Decimal('0')
			expenses = models.Expense.objects.filter(group=group).aggregate(total=Sum('amount'))['total'] or Decimal('0')
		else:
			starting = BankAccount.objects.aggregate(total=Sum('starting_balance'))['total'] if BankAccount is not None else Decimal('0')
			contribs = models.Contribution.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0')
			repayments = models.Repayment.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0')
			loan_disbursed = models.Loan.objects.filter(status='approved').aggregate(total=Sum('principal'))['total'] or Decimal('0')
			expenses = models.Expense.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0')

		starting = Decimal(starting or 0)
		contribs = Decimal(contribs)
		repayments = Decimal(repayments)
		loan_disbursed = Decimal(loan_disbursed)
		expenses = Decimal(expenses)

		bank_balance = starting + contribs + repayments - loan_disbursed - expenses

	# bank_balance already computed above (either from transactions or aggregates)
	context = {
		'total_members': total_members,
		'total_contributions': total_contributions,
		'total_loans': total_loans,
		'outstanding_loans': outstanding,
		'bank_balance': bank_balance,
	}
	return render(request, 'savingsapp/dashboard.html', context)


def landing(request):
	"""Public landing page with links to login and signup."""
	return render(request, 'savingsapp/landing2.html')


def signup(request):
	if request.method == 'POST':
		form = SignupForm(request.POST)
		if form.is_valid():
			user = form.save()
			# create initial Group for the user (if provided)
			group_name = form.cleaned_data.get('group_name')
			if group_name:
				from .models import Group
				slug = slugify(group_name)[:140]
				# ensure unique slug
				base = slug
				i = 1
				while Group.objects.filter(slug=slug).exists():
					slug = f"{base}-{i}"
					i += 1
				g = Group.objects.create(name=group_name, slug=slug, owner=user)
			messages.success(request, 'Account created. Please sign in to continue.')
			return redirect('login')
	else:
		form = SignupForm()
	return render(request, 'savingsapp/signup.html', {'form': form})

# def logout_page(request):
# 	logout(request)
# 	return redirect('login')


# def login_page(request):
# 	if request.method == 'POST':
# 		username = request.POST.get('username')
# 		password = request.POST.get('password')
# 		user = authenticate(request, username=username, password=password)
# 		if user is not None:
# 			login(request, user)
# 			return redirect('savingsapp:dashboard')
# 		else:
# 			messages.error(request, 'Invalid username or password')
# 	return render(request, 'registration/login.html')

@login_required(login_url="login")
def bank_accounts_list(request):
	qs = models.BankAccount.objects.all().order_by('name')
	return render(request, 'savingsapp/bank_accounts_list.html', {'accounts': qs})


@login_required(login_url="login")
def bank_account_detail(request, pk):
	acct = get_object_or_404(models.BankAccount, pk=pk)
	txns = acct.transactions.all()
	# compute running balance starting from starting_balance
	bal = acct.starting_balance or Decimal('0')
	for t in reversed(list(txns.order_by('date', 'created_at'))):
		bal += t.signed_amount()
	return render(request, 'savingsapp/bank_account_detail.html', {'account': acct, 'transactions': txns, 'balance': bal})


@login_required(login_url="login")
def bank_account_create(request):
	if request.method == 'POST':
		form = BankAccountForm(request.POST)
		if form.is_valid():
			acct = form.save()
			messages.success(request, 'Bank account created')
			return redirect('savingsapp:bank_accounts_list')
	else:
		form = BankAccountForm()
	return render(request, 'savingsapp/bank_account_form.html', {'form': form})


@login_required(login_url="login")
def bank_transaction_create(request):
	if request.method == 'POST':
		form = BankTransactionForm(request.POST)
		if form.is_valid():
			tx = form.save()
			messages.success(request, 'Transaction recorded')
			return redirect('savingsapp:bank_account_detail', pk=tx.account.pk)
	else:
		form = BankTransactionForm()
	return render(request, 'savingsapp/bank_transaction_form.html', {'form': form})


@login_required(login_url="login")
def members_list(request):
	q = request.GET.get('q', '').strip()
	members_qs = models.Member.objects.all().order_by('first_name', 'last_name')
	if q:
		members_qs = members_qs.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(phone__icontains=q) | Q(email__icontains=q))
	paginator = Paginator(members_qs, 25)
	page = request.GET.get('page')
	members = paginator.get_page(page)
	return render(request, 'savingsapp/members_list.html', {'members': members, 'q': q})


@login_required(login_url="login")
def member_create(request):
	if request.method == 'POST':
		form = MemberForm(request.POST)
		if form.is_valid():
			member = form.save()
			messages.success(request, 'Member created')
			return redirect('savingsapp:member_detail', pk=member.pk)
	else:
		form = MemberForm()
	return render(request, 'savingsapp/members_form.html', {'form': form})


@login_required(login_url="login")
def member_edit(request, pk):
	member = get_object_or_404(models.Member, pk=pk)
	if request.method == 'POST':
		form = MemberForm(request.POST, instance=member)
		if form.is_valid():
			form.save()
			messages.success(request, 'Member updated')
			return redirect('savingsapp:member_detail', pk=member.pk)
	else:
		form = MemberForm(instance=member)
	return render(request, 'savingsapp/members_form.html', {'form': form, 'member': member})


@login_required(login_url="login")
def member_delete(request, pk):
	member = get_object_or_404(models.Member, pk=pk)
	if request.method == 'POST':
		member.delete()
		messages.success(request, 'Member deleted')
		return redirect('savingsapp:members_list')
	return render(request, 'savingsapp/confirm_delete.html', {'object': member, 'type': 'Member'})


@login_required(login_url="login")
def members_import_csv(request):
	if request.method == 'POST' and request.FILES.get('csvfile'):
		csvfile = request.FILES['csvfile']
		data = csvfile.read().decode('utf-8')
		reader = csv.DictReader(io.StringIO(data))
		created = 0
		for row in reader:
			try:
				m, _ = models.Member.objects.get_or_create(
					first_name=row.get('first_name', '').strip(),
					last_name=row.get('last_name', '').strip(),
					defaults={'phone': row.get('phone', '').strip(), 'email': row.get('email', '').strip()}
				)
				created += 1
			except Exception:
				continue
		messages.success(request, f'Imported {created} members (duplicates skipped)')
		return redirect('savingsapp:members_list')
	return render(request, 'savingsapp/import_members.html')


@login_required(login_url="login")
def member_detail(request, pk):
	member = get_object_or_404(models.Member, pk=pk)
	memberships = member.memberships.select_related('meeting')
	contributions = models.Contribution.objects.filter(membership__member=member).order_by('-date')[:50]
	loans = models.Loan.objects.filter(membership__member=member).order_by('-created_at')[:50]
	return render(request, 'savingsapp/member_detail.html', {
		'member': member,
		'memberships': memberships,
		'contributions': contributions,
		'loans': loans,
	})


@login_required(login_url="login")
def member_statement_pdf(request, pk):
	member = get_object_or_404(models.Member, pk=pk)
	return exporters.member_statement_pdf_response(member)


@login_required(login_url="login")
def contributions_list(request):
	q = request.GET.get('q', '').strip()
	contributions_qs = models.Contribution.objects.select_related('membership__member', 'membership__meeting').order_by('-date')
	if q:
		contributions_qs = contributions_qs.filter(Q(membership__member__first_name__icontains=q) | Q(membership__member__last_name__icontains=q))
	paginator = Paginator(contributions_qs, 50)
	contributions = paginator.get_page(request.GET.get('page'))
	return render(request, 'savingsapp/contributions_list.html', {'contributions': contributions, 'q': q})


@login_required(login_url="login")
def contribution_create(request):
	if request.method == 'POST':
		form = ContributionForm(request.POST)
		if form.is_valid():
			form.save()
			messages.success(request, 'Contribution recorded')
			return redirect('savingsapp:contributions_list')
	else:
		form = ContributionForm()
	return render(request, 'savingsapp/contribution_form.html', {'form': form})


@login_required(login_url="login")
def contribution_edit(request, pk):
	contribution = get_object_or_404(models.Contribution, pk=pk)
	if request.method == 'POST':
		form = ContributionForm(request.POST, instance=contribution)
		if form.is_valid():
			form.save()
			messages.success(request, 'Contribution updated')
			return redirect('savingsapp:contributions_list')
	else:
		form = ContributionForm(instance=contribution)
	return render(request, 'savingsapp/contribution_form.html', {'form': form, 'contribution': contribution})


@login_required(login_url="login")
def contribution_delete(request, pk):
	contribution = get_object_or_404(models.Contribution, pk=pk)
	if request.method == 'POST':
		contribution.delete()
		messages.success(request, 'Contribution deleted')
		return redirect('savingsapp:contributions_list')
	return render(request, 'savingsapp/confirm_delete.html', {'object': contribution, 'type': 'Contribution'})


@login_required(login_url="login")
def loans_list(request):
	q = request.GET.get('q', '').strip()
	loans_qs = models.Loan.objects.select_related('membership__member', 'membership__meeting').order_by('-created_at')
	if q:
		loans_qs = loans_qs.filter(Q(membership__member__first_name__icontains=q) | Q(membership__member__last_name__icontains=q))
	paginator = Paginator(loans_qs, 50)
	loans = paginator.get_page(request.GET.get('page'))
	return render(request, 'savingsapp/loans_list.html', {'loans': loans, 'q': q})


@login_required(login_url="login")
def loan_create(request):
	if request.method == 'POST':
		form = LoanForm(request.POST)
		if form.is_valid():
			form.save()
			messages.success(request, 'Loan created')
			return redirect('savingsapp:loans_list')
	else:
		form = LoanForm()
	return render(request, 'savingsapp/loan_form.html', {'form': form})


@login_required(login_url="login")
def loan_edit(request, pk):
	loan = get_object_or_404(models.Loan, pk=pk)
	if request.method == 'POST':
		form = LoanForm(request.POST, instance=loan)
		if form.is_valid():
			form.save()
			messages.success(request, 'Loan updated')
			return redirect('savingsapp:loans_list')
	else:
		form = LoanForm(instance=loan)
	return render(request, 'savingsapp/loan_form.html', {'form': form, 'loan': loan})


@login_required(login_url="login")
def loan_delete(request, pk):
	loan = get_object_or_404(models.Loan, pk=pk)
	if request.method == 'POST':
		loan.delete()
		messages.success(request, 'Loan deleted')
		return redirect('savingsapp:loans_list')
	return render(request, 'savingsapp/confirm_delete.html', {'object': loan, 'type': 'Loan'})


@login_required(login_url="login")
def group_export_xlsx(request):
	# export meeting-level summary: members, contributions, loans
	qs = models.Member.objects.all().order_by('first_name')
	try:
		return exporters.group_report_xlsx(qs, filename='group_report.xlsx')
	except RuntimeError as e:
		messages.error(request, str(e))
		# fallback to simple export
		field_names = ['first_name', 'last_name', 'phone', 'email', 'joined_at']
		return exporters.queryset_to_xlsx_response(qs, field_names, filename='members_report.xlsx')


@login_required(login_url="login")
def group_export_pdf(request):
	# generate simple PDF summary for the group (all members)
	qs = models.Member.objects.all().order_by('first_name')
	# use simple CSV-style PDF: for now reuse member_statement for first member if any
	if not qs.exists():
		messages.error(request, 'No members to export')
		return redirect('savingsapp:dashboard')
	# For now, create a single PDF concatenating first 10 member statements
	from reportlab.lib.pagesizes import letter
	buffer = io.BytesIO()
	if 'reportlab' not in globals():
		try:
			from reportlab.pdfgen import canvas as _canvas
		except Exception:
			messages.error(request, 'reportlab not installed')
			return redirect('savingsapp:dashboard')
	# naive: export first member statement
	return exporters.member_statement_pdf_response(qs.first())


@login_required(login_url="login")
def expenses_list(request):
	q = request.GET.get('q', '').strip()
	expenses_qs = models.Expense.objects.select_related('meeting').order_by('-date')
	if q:
		expenses_qs = expenses_qs.filter(Q(description__icontains=q) | Q(meeting__name__icontains=q))
	paginator = Paginator(expenses_qs, 50)
	expenses = paginator.get_page(request.GET.get('page'))
	return render(request, 'savingsapp/expenses_list.html', {'expenses': expenses, 'q': q})


@login_required(login_url="login")
def expense_create(request):
	if request.method == 'POST':
		form = ExpenseForm(request.POST)
		if form.is_valid():
			form.save()
			messages.success(request, 'Expense recorded')
			return redirect('savingsapp:expenses_list')
	else:
		form = ExpenseForm()
	return render(request, 'savingsapp/expense_form.html', {'form': form})


@login_required(login_url="login")
def expense_edit(request, pk):
	exp = get_object_or_404(models.Expense, pk=pk)
	if request.method == 'POST':
		form = ExpenseForm(request.POST, instance=exp)
		if form.is_valid():
			form.save()
			messages.success(request, 'Expense updated')
			return redirect('savingsapp:expenses_list')
	else:
		form = ExpenseForm(instance=exp)
	return render(request, 'savingsapp/expense_form.html', {'form': form, 'expense': exp})


@login_required(login_url="login")
def expense_delete(request, pk):
	exp = get_object_or_404(models.Expense, pk=pk)
	if request.method == 'POST':
		exp.delete()
		messages.success(request, 'Expense deleted')
		return redirect('savingsapp:expenses_list')
	return render(request, 'savingsapp/confirm_delete.html', {'object': exp, 'type': 'Expense'})


@login_required(login_url="login")
def expenses_export_xlsx(request):
	qs = models.Expense.objects.select_related('meeting').order_by('-date')
	field_names = ['meeting', 'amount', 'description', 'date']
	return exporters.queryset_to_xlsx_response(qs, field_names, filename='expenses.xlsx')


@login_required(login_url="login")
def repayments_list(request):
	q = request.GET.get('q', '').strip()
	reps_qs = models.Repayment.objects.select_related('loan__membership__member').order_by('-date')
	if q:
		reps_qs = reps_qs.filter(Q(loan__membership__member__first_name__icontains=q) | Q(loan__membership__member__last_name__icontains=q))
	paginator = Paginator(reps_qs, 50)
	repayments = paginator.get_page(request.GET.get('page'))
	return render(request, 'savingsapp/repayments_list.html', {'repayments': repayments, 'q': q})


@login_required(login_url="login")
def repayment_create(request):
	if request.method == 'POST':
		form = RepaymentForm(request.POST)
		if form.is_valid():
			form.save()
			messages.success(request, 'Repayment recorded')
			return redirect('savingsapp:repayments_list')
	else:
		form = RepaymentForm()
	return render(request, 'savingsapp/repayment_form.html', {'form': form})


@login_required(login_url="login")
def repayment_edit(request, pk):
	rep = get_object_or_404(models.Repayment, pk=pk)
	if request.method == 'POST':
		form = RepaymentForm(request.POST, instance=rep)
		if form.is_valid():
			form.save()
			messages.success(request, 'Repayment updated')
			return redirect('savingsapp:repayments_list')
	else:
		form = RepaymentForm(instance=rep)
	return render(request, 'savingsapp/repayment_form.html', {'form': form, 'repayment': rep})


@login_required(login_url="login")
def repayment_delete(request, pk):
	rep = get_object_or_404(models.Repayment, pk=pk)
	if request.method == 'POST':
		rep.delete()
		messages.success(request, 'Repayment deleted')
		return redirect('savingsapp:repayments_list')
	return render(request, 'savingsapp/confirm_delete.html', {'object': rep, 'type': 'Repayment'})


@login_required(login_url="login")
def repayments_export_xlsx(request):
	qs = models.Repayment.objects.select_related('loan__membership__member').order_by('-date')
	field_names = ['loan', 'amount', 'date', 'note']
	return exporters.queryset_to_xlsx_response(qs, field_names, filename='repayments.xlsx')

