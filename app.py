from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, ContactMessage

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

@app.route('/login')
def login():
    return render_template('login_signup.html')

@app.route('/signup')
def signup():
    return render_template('login_signup.html')

if __name__ == '__main__':
    app.run(debug=True)