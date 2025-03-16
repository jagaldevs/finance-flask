from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, DateField, SelectField, BooleanField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, NumberRange
from datetime import datetime

class TransactionForm(FlaskForm):
    """Form for adding and editing transactions."""
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    description = StringField('Description', validators=[Optional(), Length(max=200)])
    date = DateField('Date', validators=[DataRequired()], default=datetime.now)
    category_id = SelectField('Category', validators=[DataRequired()], coerce=int)
    is_income = BooleanField('Income')
    is_recurring = BooleanField('Recurring Transaction')
    
    # Recurring transaction fields (shown conditionally via JavaScript)
    frequency = SelectField('Frequency', choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly')
    ], validators=[Optional()])
    next_date = DateField('Next Date', validators=[Optional()])
    end_date = DateField('End Date', validators=[Optional()])
    
    submit = SubmitField('Save Transaction')

class CategoryForm(FlaskForm):
    """Form for adding and editing categories."""
    name = StringField('Name', validators=[DataRequired(), Length(max=50)])
    icon = StringField('Icon', validators=[Optional(), Length(max=50)], 
                      description="Font Awesome icon name (e.g. 'utensils', 'car', 'home')")
    color = StringField('Color', validators=[Optional(), Length(max=20)],
                      description="Color in hex format (e.g. '#28a745')")
    submit = SubmitField('Save Category')