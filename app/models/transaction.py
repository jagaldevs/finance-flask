from app import db
from datetime import datetime

class Category(db.Model):
    """Category model for transaction categorization."""
    
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    icon = db.Column(db.String(50), nullable=True)
    color = db.Column(db.String(20), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    transactions = db.relationship('Transaction', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<Category {self.name}>'


class Transaction(db.Model):
    """Transaction model for financial transactions."""
    
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=True)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_income = db.Column(db.Boolean, default=False)
    is_recurring = db.Column(db.Boolean, default=False)
    
    # Relationship with RecurringTransaction
    recurring_info = db.relationship('RecurringTransaction', backref='transaction', 
                                    lazy=True, uselist=False, cascade='all, delete-orphan')
    
    def __repr__(self):
        transaction_type = "Income" if self.is_income else "Expense"
        return f'<{transaction_type} {self.amount} - {self.description}>'


class RecurringTransaction(db.Model):
    """Model for recurring transaction settings."""
    
    __tablename__ = 'recurring_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=False)
    frequency = db.Column(db.String(20), nullable=False)  # daily, weekly, monthly, yearly
    next_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<RecurringTransaction {self.frequency}>'