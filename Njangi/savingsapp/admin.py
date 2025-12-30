from django.contrib import admin
from . import models
from django.contrib import messages
from .utils import exporters


@admin.register(models.Meeting)
class MeetingAdmin(admin.ModelAdmin):
	list_display = ('name', 'year', 'start_date', 'end_date')
	search_fields = ('name', 'year')


@admin.register(models.Member)
class MemberAdmin(admin.ModelAdmin):
	list_display = ('first_name', 'last_name', 'phone', 'email', 'joined_at')
	search_fields = ('first_name', 'last_name', 'phone', 'email')
	actions = ['export_members_csv', 'export_members_xlsx', 'export_member_statement_pdf']

	def export_members_csv(self, request, queryset):
		field_names = ['first_name', 'last_name', 'phone', 'email', 'joined_at']
		return exporters.queryset_to_csv_response(queryset, field_names, filename='members.csv')

	export_members_csv.short_description = 'Export selected members to CSV'

	def export_members_xlsx(self, request, queryset):
		field_names = ['first_name', 'last_name', 'phone', 'email', 'joined_at']
		try:
			return exporters.queryset_to_xlsx_response(queryset, field_names, filename='members.xlsx')
		except RuntimeError as e:
			self.message_user(request, str(e), level=messages.ERROR)

	export_members_xlsx.short_description = 'Export selected members to Excel (.xlsx)'

	def export_member_statement_pdf(self, request, queryset):
		if queryset.count() != 1:
			self.message_user(request, 'Please select exactly one member to export a PDF statement.', level=messages.ERROR)
			return None
		member = queryset.first()
		try:
			return exporters.member_statement_pdf_response(member)
		except RuntimeError as e:
			self.message_user(request, str(e), level=messages.ERROR)

	export_member_statement_pdf.short_description = 'Export selected member statement to PDF (select one)'


@admin.register(models.Membership)
class MembershipAdmin(admin.ModelAdmin):
	list_display = ('member', 'meeting', 'monthly_due', 'is_active')
	list_filter = ('meeting', 'is_active')


@admin.register(models.Contribution)
class ContributionAdmin(admin.ModelAdmin):
	list_display = ('membership', 'amount', 'date')
	list_filter = ('date',)


@admin.register(models.Loan)
class LoanAdmin(admin.ModelAdmin):
	list_display = ('membership', 'principal', 'interest_rate', 'status', 'due_date')
	list_filter = ('status', 'due_date')
	search_fields = ('membership__member__first_name', 'membership__member__last_name')


@admin.register(models.Repayment)
class RepaymentAdmin(admin.ModelAdmin):
	list_display = ('loan', 'amount', 'date')
	list_filter = ('date',)


@admin.register(models.Expense)
class ExpenseAdmin(admin.ModelAdmin):
	list_display = ('meeting', 'amount', 'date', 'description')
	list_filter = ('date',)


@admin.register(models.YearEndDistribution)
class YearEndDistributionAdmin(admin.ModelAdmin):
	list_display = ('meeting', 'member', 'year', 'total_returned')
	list_filter = ('year', 'meeting')


class BankAccountAdmin(admin.ModelAdmin):
	list_display = ('name', 'account_number', 'starting_balance', 'created_at')
	search_fields = ('name', 'account_number')

try:
	admin.site.register(models.BankAccount, BankAccountAdmin)
except Exception:
	# If BankAccount model isn't available (import order/migration issues), skip registration.
	pass


try:
	@admin.register(models.BankTransaction)
	class BankTransactionAdmin(admin.ModelAdmin):
		list_display = ('account', 'date', 'kind', 'amount', 'category', 'reference')
		list_filter = ('kind', 'date', 'category')
		search_fields = ('account__name', 'reference', 'category')
except Exception:
	# migrations/import-time safety
	pass
