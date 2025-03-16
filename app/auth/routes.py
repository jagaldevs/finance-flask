from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.models.user import User
from app.auth.forms import LoginForm, RegistrationForm
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login page."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            
            # Update last login time
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard.dashboard'))
        
        flash('Invalid email or password', 'danger')
    
    return render_template('auth/login.html', form=form, title='Login')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        
        # Add default categories
        from app.models.transaction import Category
        default_categories = [
            Category(name='Food', icon='utensils', color='#28a745', user=user),
            Category(name='Restaurant & Café', icon='coffee', color='#dc3545', user=user),
            Category(name='Fuel', icon='gas-pump', color='#fd7e14', user=user),
            Category(name='Kindergarten', icon='child', color='#6f42c1', user=user),
            Category(name='Rent', icon='home', color='#17a2b8', user=user),
            Category(name='Other', icon='tag', color='#6c757d', user=user)
        ]
        
        db.session.add(user)
        for category in default_categories:
            db.session.add(category)
        
        db.session.commit()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form, title='Register')

@auth_bp.route('/logout')
@login_required
def logout():
    """Logout route."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))