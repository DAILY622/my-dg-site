from django.urls import path
from . import views

app_name = 'investments'

urlpatterns = [
    path('plans/', views.plans_list, name='plans'),
    path('sectors/<str:sector>/', views.sector_page, name='sector'),
    path('buy-shares/', views.buy_shares, name='buy_shares'),
    path('invest/<int:plan_id>/', views.create_investment, name='invest'),
    path('my-investments/', views.my_investments, name='my_investments'),
    path('deposit/', views.deposit_view, name='deposit'),
    path('deposit-status/<int:deposit_id>/', views.deposit_status, name='deposit_status'),
    path('pending-payment/<int:deposit_id>/', views.pending_payment, name='pending_payment'),
    path('payment-confirmed/<int:deposit_id>/', views.payment_confirmed, name='payment_confirmed'),
    path('withdraw/', views.withdraw_view, name='withdraw'),
    path('loans/', views.loan_application, name='loans'),
    path('loans/<int:loan_id>/repay/', views.loan_repay, name='loan_repay'),
    path('cards/', views.virtual_cards, name='cards'),
    path('cards/freeze/', views.freeze_card, name='freeze_card'),
    path('cards/unfreeze/', views.unfreeze_card, name='unfreeze_card'),
    path('cards/topup/', views.top_up_card, name='top_up_card'),
    path('cards/replace/', views.replace_card, name='replace_card'),
    path('cards/transactions/', views.card_transactions, name='card_transactions'),
    path('agent/', views.agent_page, name='agent'),
    
    # PDF Receipt Downloads
    path('receipt/deposit/<int:deposit_id>/download/', views.download_deposit_receipt, name='download_deposit_receipt'),
    path('receipt/investment/<int:investment_id>/download/', views.download_investment_receipt, name='download_investment_receipt'),
    path('receipt/withdrawal/<int:withdrawal_id>/download/', views.download_withdrawal_receipt, name='download_withdrawal_receipt'),
    path('receipt/deposit/<int:deposit_id>/', views.view_deposit_receipt, name='view_deposit_receipt'),
    path('receipt/investment/<int:investment_id>/', views.view_investment_receipt, name='view_investment_receipt'),
    
    # API endpoints
    path('api/ticker/', views.crypto_ticker_api, name='crypto_ticker_api'),
    path('api/deposit-status/<int:deposit_id>/', views.check_deposit_status_api, name='check_deposit_status'),
]
