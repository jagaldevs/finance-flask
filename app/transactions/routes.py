from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.transaction import Transaction, Category, RecurringTransaction
from app.transactions.forms import TransactionForm, CategoryForm
from datetime import datetime

transaction_bp = Blueprint('transactions', __name__, url_prefix='/transactions')

@transaction_bp.route('/', methods=['GET'])
@login_required
def list():
    """List all transactions."""
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    type_filter = request.args.get('type', 'all')
    category_id = request.args.get('category', None, type=int)
    
    # Build query
    query = Transaction.query.filter_by(user_id=current_user.id)
    
    # Apply filters
    if type_filter == 'expense':
        query = query.filter_by(is_income=False)
    elif type_filter == 'income':
        query = query.filter_by(is_income=True)
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    # Get transactions with pagination
    transactions = query.order_by(Transaction.date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get categories for filter dropdown
    categories = Category.query.filter_by(user_id=current_user.id).all()
    
    return render_template(
        'transactions/list.html',
        transactions=transactions,
        categories=categories,
        type_filter=type_filter,
        category_id=category_id
    )

@transaction_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    """Add a new transaction."""
    form = TransactionForm()
    
    # Populate category choices
    form.category_id.choices = [
        (c.id, c.name) for c in Category.query.filter_by(user_id=current_user.id).all()
    ]
    
    if form.validate_on_submit():
        transaction = Transaction(
            amount=form.amount.data,
            description=form.description.data,
            date=form.date.data,
            category_id=form.category_id.data,
            user_id=current_user.id,
            is_income=form.is_income.data,
            is_recurring=form.is_recurring.data
        )
        
        db.session.add(transaction)
        
        # Add recurring transaction info if applicable
        if form.is_recurring.data:
            recurring = RecurringTransaction(
                transaction=transaction,
                frequency=form.frequency.data,
                next_date=form.next_date.data,
                end_date=form.end_date.data
            )
            db.session.add(recurring)
        
        db.session.commit()
        flash('Transaction added successfully.', 'success')
        return redirect(url_for('transactions.list'))
    
    return render_template('transactions/form.html', form=form, title='Add Transaction')

@transaction_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit an existing transaction."""
    transaction = Transaction.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    form = TransactionForm(obj=transaction)
    
    # Populate category choices
    form.category_id.choices = [
        (c.id, c.name) for c in Category.query.filter_by(user_id=current_user.id).all()
    ]
    
    if form.validate_on_submit():
        transaction.amount = form.amount.data
        transaction.description = form.description.data
        transaction.date = form.date.data
        transaction.category_id = form.category_id.data
        transaction.is_income = form.is_income.data
        transaction.is_recurring = form.is_recurring.data
        
        # Update or create recurring transaction info if applicable
        if form.is_recurring.data:
            if transaction.recurring_info:
                transaction.recurring_info.frequency = form.frequency.data
                transaction.recurring_info.next_date = form.next_date.data
                transaction.recurring_info.end_date = form.end_date.data
            else:
                recurring = RecurringTransaction(
                    transaction=transaction,
                    frequency=form.frequency.data,
                    next_date=form.next_date.data,
                    end_date=form.end_date.data
                )
                db.session.add(recurring)
        elif transaction.recurring_info:
            # Remove recurring info if transaction is no longer recurring
            db.session.delete(transaction.recurring_info)
        
        db.session.commit()
        flash('Transaction updated successfully.', 'success')
        return redirect(url_for('transactions.list'))
    
    # Pre-fill recurring transaction data if applicable
    if transaction.recurring_info:
        form.frequency.data = transaction.recurring_info.frequency
        form.next_date.data = transaction.recurring_info.next_date
        form.end_date.data = transaction.recurring_info.end_date
    
    return render_template('transactions/form.html', form=form, title='Edit Transaction')

@transaction_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    """Delete a transaction."""
    transaction = Transaction.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    db.session.delete(transaction)
    db.session.commit()
    
    flash('Transaction deleted successfully.', 'success')
    return redirect(url_for('transactions.list'))

@transaction_bp.route('/categories', methods=['GET', 'POST'])
@login_required
def categories():
    """List and manage categories."""
    categories = Category.query.filter_by(user_id=current_user.id).all()
    form = CategoryForm()
    
    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            icon=form.icon.data,
            color=form.color.data,
            user_id=current_user.id
        )
        
        db.session.add(category)
        db.session.commit()
        
        flash('Category added successfully.', 'success')
        return redirect(url_for('transactions.categories'))
    
    return render_template(
        'transactions/categories.html',
        categories=categories,
        form=form
    )

@transaction_bp.route('/categories/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_category(id):
    """Edit an existing category."""
    category = Category.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    form = CategoryForm(obj=category)
    
    if form.validate_on_submit():
        category.name = form.name.data
        category.icon = form.icon.data
        category.color = form.color.data
        
        db.session.commit()
        flash('Category updated successfully.', 'success')
        return redirect(url_for('transactions.categories'))
    
    return render_template(
        'transactions/edit_category.html',
        category=category,
        form=form
    )

@transaction_bp.route('/categories/delete/<int:id>', methods=['POST'])
@login_required
def delete_category(id):
    """Delete a category."""
    category = Category.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    # Check if category has transactions
    if Transaction.query.filter_by(category_id=category.id).first():
        flash('Cannot delete category with existing transactions.', 'danger')
        return redirect(url_for('transactions.categories'))
    
    db.session.delete(category)
    db.session.commit()
    
    flash('Category deleted successfully.', 'success')
    return redirect(url_for('transactions.categories'))