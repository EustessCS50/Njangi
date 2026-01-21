from django.urls import path, include
from rest_framework import routers
from .views import (
    MemberViewSet, MembershipViewSet, ContributionViewSet, LoanViewSet,
    RepaymentViewSet, ExpenseViewSet, BankAccountViewSet, BankTransactionViewSet, MeetingsViewSet,
    api_help, GroupViewSet,
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = routers.DefaultRouter()
router.register(r'members', MemberViewSet)
router.register(r'memberships', MembershipViewSet)
router.register(r'meetings', MeetingsViewSet)
router.register(r'contributions', ContributionViewSet)
router.register(r'loans', LoanViewSet)
router.register(r'repayments', RepaymentViewSet)
router.register(r'expenses', ExpenseViewSet)
router.register(r'bank/accounts', BankAccountViewSet)
router.register(r'bank/transactions', BankTransactionViewSet)
router.register(r'groups', GroupViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('help/', api_help, name='api_help'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
