from django.urls import path, include
from . import views

app_name = 'savingsapp'

urlpatterns = [
    path('', views.landing, name='landing'),
    path('signup/', views.signup, name='signup'),
    # path('login/', views.login_page, name='login'),
    # path('logout/', views.logout_page, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('members/', views.members_list, name='members_list'),
    path('members/<int:pk>/', views.member_detail, name='member_detail'),
    path('members/<int:pk>/statement_pdf/', views.member_statement_pdf, name='member_statement_pdf'),
    path('members/add/', views.member_create, name='member_create'),
    path('members/<int:pk>/edit/', views.member_edit, name='member_edit'),
    path('members/<int:pk>/delete/', views.member_delete, name='member_delete'),
    path('members/import/', views.members_import_csv, name='members_import_csv'),
    path('contributions/', views.contributions_list, name='contributions_list'),
    path('loans/', views.loans_list, name='loans_list'),
    path('contributions/add/', views.contribution_create, name='contribution_create'),
        path('contributions/<int:pk>/edit/', views.contribution_edit, name='contribution_edit'),
        path('contributions/<int:pk>/delete/', views.contribution_delete, name='contribution_delete'),
    path('loans/add/', views.loan_create, name='loan_create'),
        path('loans/<int:pk>/edit/', views.loan_edit, name='loan_edit'),
        path('loans/<int:pk>/delete/', views.loan_delete, name='loan_delete'),
        # Expenses
        path('expenses/', views.expenses_list, name='expenses_list'),
        path('expenses/add/', views.expense_create, name='expense_create'),
        path('expenses/<int:pk>/edit/', views.expense_edit, name='expense_edit'),
        path('expenses/<int:pk>/delete/', views.expense_delete, name='expense_delete'),
        path('expenses/export_xlsx/', views.expenses_export_xlsx, name='expenses_export_xlsx'),
        # Repayments
        path('repayments/', views.repayments_list, name='repayments_list'),
        path('repayments/add/', views.repayment_create, name='repayment_create'),
        path('repayments/<int:pk>/edit/', views.repayment_edit, name='repayment_edit'),
        path('repayments/<int:pk>/delete/', views.repayment_delete, name='repayment_delete'),
        path('repayments/export_xlsx/', views.repayments_export_xlsx, name='repayments_export_xlsx'),
    path('reports/export_xlsx/', views.group_export_xlsx, name='group_export_xlsx'),
    path('reports/export_pdf/', views.group_export_pdf, name='group_export_pdf'),
    # API
    path('api/', include('savingsapp.api.urls')),
        # Bank accounts
        path('bank/accounts/', views.bank_accounts_list, name='bank_accounts_list'),
        path('bank/accounts/add/', views.bank_account_create, name='bank_account_create'),
        path('bank/accounts/<int:pk>/', views.bank_account_detail, name='bank_account_detail'),
        path('bank/transactions/add/', views.bank_transaction_create, name='bank_transaction_create'),
]
