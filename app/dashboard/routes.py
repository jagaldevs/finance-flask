from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app.models.transaction import Transaction, Category
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from app import db
import calendar

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/', methods=['GET'])
@login_required
def dashboard():
    """Dashboard homepage with financial overview."""
    return render_template('dashboard/index.html')

@dashboard_bp.route('/data', methods=['GET'])
@login_required
def dashboard_data():
    """API endpoint for dashboard data."""
    # Get time range from request
    time_range = request.args.get('range', 'month')
    
    # Calculate date ranges
    today = datetime.utcnow().date()
    
    if time_range == 'month':
        start_date = today.replace(day=1)
    elif time_range == '3months':
        # Go back 3 months
        three_months_ago = today.month - 3
        year_offset = 0
        if three_months_ago <= 0:
            three_months_ago += 12
            year_offset = -1
        start_date = today.replace(year=today.year + year_offset, month=three_months_ago, day=1)
    elif time_range == 'custom':
        # Parse custom date range if provided
        try:
            start_date = datetime.strptime(request.args.get('start', ''), '%Y-%m-%d').date()
            end_date = datetime.strptime(request.args.get('end', ''), '%Y-%m-%d').date()
        except ValueError:
            start_date = today - timedelta(days=30)
            end_date = today
    else:
        # Default to last 30 days
        start_date = today - timedelta(days=30)
    
    if time_range != 'custom':
        end_date = today
    
    if time_range != 'custom':
        end_date = today
    
    # Query data for the dashboard
    data = {}
    
    # Total expenses for the period
    total_expenses = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.is_income == False,
        Transaction.date >= start_date,
        Transaction.date <= end_date
    ).with_entities(func.sum(Transaction.amount)).scalar() or 0
    
    # Total income for the period
    total_income = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.is_income == True,
        Transaction.date >= start_date,
        Transaction.date <= end_date
    ).with_entities(func.sum(Transaction.amount)).scalar() or 0
    
    # Today's expenses
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    today_expenses = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.is_income == False,
        Transaction.date >= today_start,
        Transaction.date <= today_end
    ).with_entities(func.sum(Transaction.amount)).scalar() or 0
    
    # Expenses by category
    category_expenses = db.session.query(
        Category.name, 
        Category.color,
        func.sum(Transaction.amount)
    ).join(Transaction).filter(
        Transaction.user_id == current_user.id,
        Transaction.is_income == False,
        Transaction.date >= start_date,
        Transaction.date <= end_date
    ).group_by(Category.id).all()
    
    # Recent transactions
    recent_transactions = Transaction.query.filter(
        Transaction.user_id == current_user.id
    ).order_by(Transaction.date.desc()).limit(5).all()
    
    # Transaction frequency
    # Daily average
    days_count = (end_date - start_date).days + 1
    daily_avg = round(Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.date >= start_date,
        Transaction.date <= end_date
    ).count() / days_count, 1)
    
    # Weekly average
    weeks_count = days_count / 7
    weekly_avg = round(Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.date >= start_date,
        Transaction.date <= end_date
    ).count() / weeks_count, 1)
    
    # Prepare response data
    data = {
        'total_expenses': round(total_expenses, 2),
        'total_income': round(total_income, 2),
        'today_expenses': round(today_expenses, 2),
        'category_expenses': [
            {
                'name': cat[0],
                'color': cat[1],
                'amount': round(cat[2], 2)
            } for cat in category_expenses
        ],
        'transaction_frequency': {
            'daily': daily_avg,
            'weekly': weekly_avg
        }
    }
    
    return jsonify(data)

@dashboard_bp.route('/chart-data', methods=['GET'])
@login_required
def chart_data():
    """API endpoint for chart data."""
    # Get time range from request
    time_range = request.args.get('range', 'month')
    chart_type = request.args.get('type', 'expenses_income')
    
    # Calculate date ranges
    today = datetime.utcnow().date()
    
    if time_range == 'month':
        start_date = today.replace(day=1)
    elif time_range == '3months':
        # Go back 3 months
        three_months_ago = today.month - 3
        year_offset = 0
        if three_months_ago <= 0:
            three_months_ago += 12
            year_offset = -1
        start_date = today.replace(year=today.year + year_offset, month=three_months_ago, day=1)
    elif time_range == 'custom':
        # Parse custom date range if provided
        try:
            start_date = datetime.strptime(request.args.get('start', ''), '%Y-%m-%d').date()
            end_date = datetime.strptime(request.args.get('end', ''), '%Y-%m-%d').date()
        except ValueError:
            start_date = today - timedelta(days=30)
            end_date = today
    elif time_range == 'year':
        start_date = today.replace(month=1, day=1)
    else:
        # Default to last 30 days
        start_date = today - timedelta(days=30)
    
    if time_range != 'custom':
        end_date = today
    
    data = {}
    
    if chart_type == 'expenses_income':
        # Get expenses and income over time for line chart
        expenses_data = []
        income_data = []
        
        # For month view, group by day
        if time_range in ['week', 'month']:
            # Initialize cumulative totals
            cumulative_expense = 0
            cumulative_income = 0
            
            for i in range((end_date - start_date).days + 1):
                current_date = start_date + timedelta(days=i)
                next_date = current_date + timedelta(days=1)
                
                # Daily expenses
                daily_expense = Transaction.query.filter(
                    Transaction.user_id == current_user.id,
                    Transaction.is_income == False,
                    Transaction.date >= datetime.combine(current_date, datetime.min.time()),
                    Transaction.date < datetime.combine(next_date, datetime.min.time())
                ).with_entities(func.sum(Transaction.amount)).scalar() or 0
                
                # Daily income
                daily_income = Transaction.query.filter(
                    Transaction.user_id == current_user.id,
                    Transaction.is_income == True,
                    Transaction.date >= datetime.combine(current_date, datetime.min.time()),
                    Transaction.date < datetime.combine(next_date, datetime.min.time())
                ).with_entities(func.sum(Transaction.amount)).scalar() or 0
                
                # Add to cumulative totals
                cumulative_expense += daily_expense
                cumulative_income += daily_income
                
                expenses_data.append({
                    'date': current_date.strftime('%d.%m'),
                    'amount': round(cumulative_expense, 2)
                })
                
                income_data.append({
                    'date': current_date.strftime('%d.%m'),
                    'amount': round(cumulative_income, 2)
                })
                
        # For year view, group by month
        elif time_range == 'year':
            # Initialize cumulative totals
            cumulative_expense = 0
            cumulative_income = 0
            
            for month in range(1, 13):
                start_of_month = datetime(today.year, month, 1)
                
                if month == 12:
                    end_of_month = datetime(today.year + 1, 1, 1) - timedelta(days=1)
                else:
                    end_of_month = datetime(today.year, month + 1, 1) - timedelta(days=1)
                
                # Monthly expenses
                monthly_expense = Transaction.query.filter(
                    Transaction.user_id == current_user.id,
                    Transaction.is_income == False,
                    Transaction.date >= start_of_month,
                    Transaction.date <= end_of_month
                ).with_entities(func.sum(Transaction.amount)).scalar() or 0
                
                # Monthly income
                monthly_income = Transaction.query.filter(
                    Transaction.user_id == current_user.id,
                    Transaction.is_income == True,
                    Transaction.date >= start_of_month,
                    Transaction.date <= end_of_month
                ).with_entities(func.sum(Transaction.amount)).scalar() or 0
                
                # Add to cumulative totals
                cumulative_expense += monthly_expense
                cumulative_income += monthly_income
                
                expenses_data.append({
                    'date': start_of_month.strftime('%b'),
                    'amount': round(cumulative_expense, 2)
                })
                
                income_data.append({
                    'date': start_of_month.strftime('%b'),
                    'amount': round(cumulative_income, 2)
                })
        
        data = {
            'expenses': expenses_data,
            'income': income_data
        }
    
    elif chart_type == 'category_breakdown':
        # Get category breakdown for pie/radar chart
        category_data = db.session.query(
            Category.name, 
            Category.color,
            func.sum(Transaction.amount)
        ).join(Transaction).filter(
            Transaction.user_id == current_user.id,
            Transaction.is_income == False,
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).group_by(Category.id).all()
        
        data = [
            {
                'name': cat[0],
                'color': cat[1],
                'amount': round(cat[2], 2)
            } for cat in category_data
        ]
    
    return jsonify(data)
