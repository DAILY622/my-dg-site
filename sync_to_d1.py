"""
SYNC USERS FROM POSTGRESQL TO CLOUDFLARE D1

This script syncs user portfolio data from PostgreSQL to D1 edge database
for faster global access.

Run with: python manage.py shell < sync_to_d1.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elite_wealth_capital.settings')
django.setup()

from django.contrib.auth import get_user_model
from investments.models import Investment, Deposit, Withdrawal
from django.db.models import Sum, Count, Q
import requests

User = get_user_model()

# Cloudflare Worker URL
WORKER_URL = "https://elite-wealth-worker.bthailand998.workers.dev"

def sync_user_to_d1(user):
    """Sync a single user's portfolio to D1"""
    
    # Calculate portfolio stats
    total_invested = Investment.objects.filter(
        user=user,
        status__in=['active', 'completed']
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    total_profit = Investment.objects.filter(
        user=user,
        status='completed'
    ).aggregate(Sum('profit'))['profit__sum'] or 0
    
    active_investments = Investment.objects.filter(
        user=user,
        status='active'
    ).count()
    
    completed_investments = Investment.objects.filter(
        user=user,
        status='completed'
    ).count()
    
    # Get completed investments for history
    completed = Investment.objects.filter(
        user=user,
        status='completed'
    ).order_by('-created_at')[:20]  # Last 20
    
    print(f"User {user.id} ({user.email}):")
    print(f"  Total Invested: ${total_invested}")
    print(f"  Total Profit: ${total_profit}")
    print(f"  Active: {active_investments}, Completed: {completed_investments}")
    
    return {
        'user_id': user.id,
        'total_invested': float(total_invested),
        'total_profit': float(total_profit),
        'active_investments': active_investments,
        'completed_investments': completed_investments,
        'history': [
            {
                'plan_name': inv.plan.name if inv.plan else 'Unknown',
                'amount': float(inv.amount),
                'profit': float(inv.profit or 0),
                'roi_percentage': float(inv.plan.roi_percentage if inv.plan else 0),
                'start_date': inv.created_at.strftime('%Y-%m-%d'),
                'end_date': inv.maturity_date.strftime('%Y-%m-%d') if inv.maturity_date else '',
            }
            for inv in completed
        ]
    }

def main():
    print("\n" + "="*60)
    print("🔄 SYNCING USERS FROM POSTGRESQL TO CLOUDFLARE D1")
    print("="*60 + "\n")
    
    # Get all users
    users = User.objects.all().order_by('id')
    total_users = users.count()
    
    print(f"Found {total_users} users in PostgreSQL\n")
    
    # Collect all portfolio data
    portfolios = []
    
    for idx, user in enumerate(users, 1):
        print(f"[{idx}/{total_users}] Processing {user.email}...")
        try:
            portfolio_data = sync_user_to_d1(user)
            portfolios.append(portfolio_data)
        except Exception as e:
            print(f"  ❌ Error: {e}")
            continue
    
    print(f"\n✅ Prepared {len(portfolios)} portfolios")
    
    # Generate SQL for D1
    print("\n" + "="*60)
    print("📝 GENERATING D1 SQL INSERT STATEMENTS")
    print("="*60 + "\n")
    
    sql_statements = []
    
    # Delete existing data
    sql_statements.append("DELETE FROM portfolios;")
    sql_statements.append("DELETE FROM investment_history;")
    
    # Insert portfolios
    for portfolio in portfolios:
        sql = f"""INSERT INTO portfolios (user_id, total_invested, total_profit, active_investments, completed_investments)
VALUES ({portfolio['user_id']}, {portfolio['total_invested']}, {portfolio['total_profit']}, {portfolio['active_investments']}, {portfolio['completed_investments']})
ON CONFLICT(user_id) DO UPDATE SET
  total_invested = {portfolio['total_invested']},
  total_profit = {portfolio['total_profit']},
  active_investments = {portfolio['active_investments']},
  completed_investments = {portfolio['completed_investments']},
  last_updated = CURRENT_TIMESTAMP;"""
        sql_statements.append(sql)
        
        # Insert investment history
        for hist in portfolio['history']:
            hist_sql = f"""INSERT INTO investment_history (user_id, plan_name, amount, profit, roi_percentage, start_date, end_date, status)
VALUES ({portfolio['user_id']}, '{hist['plan_name'].replace("'", "''")}', {hist['amount']}, {hist['profit']}, {hist['roi_percentage']}, '{hist['start_date']}', '{hist['end_date']}', 'completed');"""
            sql_statements.append(hist_sql)
    
    # Save SQL to file
    output_file = 'sync_users_to_d1.sql'
    with open(output_file, 'w') as f:
        f.write('\n\n'.join(sql_statements))
    
    print(f"✅ Generated {len(sql_statements)} SQL statements")
    print(f"✅ Saved to: {output_file}\n")
    
    print("="*60)
    print("🚀 NEXT STEPS:")
    print("="*60 + "\n")
    print("Run this command to sync to D1:")
    print(f"  cd cloudflare-worker")
    print(f"  wrangler d1 execute elite-portfolios --remote --file=../sync_users_to_d1.sql")
    print()
    
    return len(portfolios)

if __name__ == '__main__':
    try:
        count = main()
        print(f"✅ Successfully prepared {count} user portfolios for D1 sync!\n")
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
