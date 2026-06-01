from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, session
)
from models import db, User, ContactMessage
from functools import wraps
app = Flask(__name__)

# ── Config ──
app.config['SECRET_KEY']          = 'TabShama2014&TabPeneal2016&TabRussel2018&TabQueency2020&'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cybershield.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ── Init DB ──
db.init_app(app)

with app.app_context():
    db.create_all()  

# ── Routes ──
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated
  
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():

    if request.method == 'POST':

        full_name = request.form.get('full_name', '').strip()
        email     = request.form.get('email', '').strip()
        subject   = request.form.get('subject', '').strip()
        message   = request.form.get('message', '').strip()

        # ── Server-side validation ──
        errors = []

        if not full_name:
            errors.append('Full name is required.')
        if not email or '@' not in email:
            errors.append('A valid email address is required.')
        if not subject:
            errors.append('Please select a subject.')
        if not message or len(message) < 10:
            errors.append('Message must be at least 10 characters.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return redirect(url_for('contact'))

        # ── Save to DB ──
        new_message = ContactMessage(
            full_name  = full_name,
            email      = email,
            subject    = subject,
            message    = message,
            ip_address = request.remote_addr
        )

        db.session.add(new_message)
        db.session.commit()

        flash('Message received. Our team will respond shortly.', 'success')
        return redirect(url_for('contact'))

    return render_template('contact.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please enter your email and password.', 'error')
            return redirect(url_for('login'))

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash('Invalid credentials. Access denied.', 'error')
            return redirect(url_for('login'))

        if not user.is_active:
            flash('This account has been deactivated.', 'error')
            return redirect(url_for('login'))

        # ✅ Save session
        session['user_id']   = user.id
        session['user_name'] = f'{user.first_name} {user.last_name}'
        session['user_role'] = user.role
        session['user_email']= user.email

        flash(f'Welcome back, {user.first_name}. Session initialized.', 'success')
        return redirect(url_for('home'))

    return render_template('login_signup.html', mode='login')

# ── Register ──
@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        first_name       = request.form.get('first_name', '').strip()
        last_name        = request.form.get('last_name', '').strip()
        email            = request.form.get('email', '').strip().lower()
        password         = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role             = request.form.get('role', 'student')

        # ── Validation ──
        errors = []

        if not first_name:
            errors.append('First name is required.')
        if not last_name:
            errors.append('Last name is required.')
        if not email or '@' not in email:
            errors.append('A valid email is required.')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        if User.query.filter_by(email=email).first():
            errors.append('An account with this email already exists.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return redirect(url_for('register'))

        # ✅ Create user
        new_user = User(
            first_name = first_name,
            last_name  = last_name,
            email      = email,
            role       = role
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully. You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('login_signup.html', mode='register')

# ── Logout ──
@app.route('/logout')
def logout():
    session.clear()
    flash('Session terminated. You have been logged out.', 'success')
    return redirect(url_for('login'))

# # ── Dashboard (protected) ──
# @app.route('/dashboard')
# @login_required
# def dashboard():
#     return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(debug=True)