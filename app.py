from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, session
)
from models import db, User, ContactMessage, Enrollment, Course, Lab, LabProgress, LiveEvent
from functools import wraps
from datetime import datetime
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SECRET_KEY']                     = 'TabShama2014&TabPenel2016&TabRussel2018&TabQueency2020&'
app.config['SQLALCHEMY_DATABASE_URI']        = 'sqlite:///cybershield.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
migrate = Migrate(app, db)
db.init_app(app)

with app.app_context():
    db.create_all()

# ── Hardcoded admin credentials ──
ADMIN_EMAIL    = 'admin@cybershield.io'
ADMIN_PASSWORD = 'CyberAdmin#2025'


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('user_role') != 'admin':
            flash('Access denied. Admin only.', 'error')
            return redirect(url_for('student_dashboard'))
        return f(*args, **kwargs)
    return decorated

def _enrich_labs(labs):
    """Attach .user_progress to every lab for the current session user."""
    if 'user_id' not in session or session.get('user_role') == 'admin':
        for lab in labs:
            lab.user_progress = None
        return labs

    lab_ids = [lab.id for lab in labs]
    progress_map = {
        p.lab_id: p
        for p in LabProgress.query.filter(
            LabProgress.user_id == session['user_id'],
            LabProgress.lab_id.in_(lab_ids)
        ).all()
    }
    for lab in labs:
        lab.user_progress = progress_map.get(lab.id)
    return labs

def _labs_stats():
    """Return stat-card numbers for the labs page."""
    total_labs = Lab.query.filter_by(is_active=True).count()
    if 'user_id' not in session or session.get('user_role') == 'admin':
        return dict(total_labs=total_labs, completed=0, in_progress=0, xp_earned=0)

    all_prog = LabProgress.query.filter_by(user_id=session['user_id']).all()
    return dict(
        total_labs  = total_labs,
        completed   = sum(1 for p in all_prog if p.completed),
        in_progress = sum(1 for p in all_prog if not p.completed and p.percent > 0),
        xp_earned   = sum(p.xp_awarded for p in all_prog if p.completed),
    )

def _course_stats():
    """Stat-card numbers for the courses page."""
    total = Course.query.count()
    if 'user_id' not in session or session.get('user_role') == 'admin':
        return dict(total=total, enrolled=0, in_progress=0, completed=0)

    all_enroll = Enrollment.query.filter_by(user_id=session['user_id']).all()
    return dict(
        total       = total,
        enrolled    = len(all_enroll),
        in_progress = sum(1 for e in all_enroll if 0 < e.progress < 100),
        completed   = sum(1 for e in all_enroll if e.progress == 100),
    )

def _enrolled_map():
    """Return {course_id: Enrollment} for the logged-in student."""
    if 'user_id' not in session or session.get('user_role') == 'admin':
        return {}
    rows = Enrollment.query.filter_by(user_id=session['user_id']).all()
    return {e.course_id: e for e in rows}

# ── Home ──
@app.route('/')
def home():
    return render_template('index.html')

# ── About ──
@app.route('/about')
def about():
    return render_template('about.html')

# ── Login ──
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        if session.get('user_role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('student_dashboard'))

    if request.method == 'POST':
        role     = request.form.get('role', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please enter your email and password.', 'error')
            return redirect(url_for('login'))

        # ── Admin login ──
        if role == 'admin':
            if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
                session['user_id']    = 0
                session['user_name']  = 'Admin'
                session['user_role']  = 'admin'
                session['user_email'] = ADMIN_EMAIL
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Invalid admin credentials. Access denied.', 'error')
                return redirect(url_for('login'))

        # ── Student login ──
        if role == 'student':
            user = User.query.filter_by(email=email, role='student').first()
            if not user or not user.check_password(password):
                flash('Invalid credentials. Access denied.', 'error')
                return redirect(url_for('login'))
            if not user.is_active:
                flash('This account has been deactivated.', 'error')
                return redirect(url_for('login'))

            session['user_id']    = user.id
            session['user_name']  = f'{user.first_name} {user.last_name}'
            session['user_role']  = 'student'
            session['user_email'] = user.email
            flash(f'Welcome back, {user.first_name}. Session initialized.', 'success')
            return redirect(url_for('student_dashboard'))

        flash('Please select a valid role.', 'error')
        return redirect(url_for('login'))

    return render_template('login_signup.html', mode='login')

# ── Register (students only) ──
@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('student_dashboard'))

    if request.method == 'POST':
        first_name       = request.form.get('first_name', '').strip()
        last_name        = request.form.get('last_name', '').strip()
        email            = request.form.get('email', '').strip().lower()
        password         = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        errors = []
        if not first_name:              errors.append('First name is required.')
        if not last_name:               errors.append('Last name is required.')
        if not email or '@' not in email: errors.append('A valid email is required.')
        if len(password) < 8:           errors.append('Password must be at least 8 characters.')
        if password != confirm_password: errors.append('Passwords do not match.')
        if User.query.filter_by(email=email).first():
            errors.append('An account with this email already exists.')

        if errors:
            for e in errors:
                flash(e, 'error')
            return redirect(url_for('register'))

        new_user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            role='student'
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

# ── Student dashboard ──
@app.route('/dashboard')
@login_required
def student_dashboard():
    if session.get('user_role') == 'admin':
        return redirect(url_for('admin_dashboard'))
    user = User.query.get(session['user_id'])
    enrollments = Enrollment.query.filter_by(user_id=session['user_id']).all()
    return render_template('dashboard.html', user=user, enrollments=enrollments)

# ── Admin dashboard ──
@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    total_students = User.query.filter_by(role='student').count()
    users = User.query.filter_by(role='student').all()
    active_students = User.query.filter_by(role='student', is_active=True).count()
    total_messages = ContactMessage.query.count()
    new_messages = ContactMessage.query.filter_by(is_read=False).count()
    recent_users = User.query.filter_by(role='student').order_by(User.created_at.desc()).limit(8).all()
    recent_messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(5).all()
    return render_template('admin_dashboard.html',
        total_students=total_students,
        active_students=active_students,
        total_messages=total_messages,
        new_messages=new_messages,
        recent_users=recent_users,
        recent_messages=recent_messages,
        unread_count=new_messages,
        users=users
    )

# ── Admin: all messages ──
@app.route('/admin/messages')
@login_required
@admin_required
def admin_messages():
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    for m in messages:
        m.is_read = True
    db.session.commit()
    return render_template('admin_messages.html', messages=messages)

# ── Admin: toggle user active ──
@app.route('/admin/user/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    flash(f'User {"activated" if user.is_active else "deactivated"} successfully.', 'success')
    return redirect(url_for('admin_dashboard'))

# ── Contact ──
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email     = request.form.get('email', '').strip()
        subject   = request.form.get('subject', '').strip()
        message   = request.form.get('message', '').strip()

        errors = []
        if not full_name:         errors.append('Full name is required.')
        if not email:             errors.append('Email is required.')
        if not subject:           errors.append('Please select a subject.')
        if len(message) < 10:     errors.append('Message must be at least 10 characters.')

        if errors:
            for e in errors:
                flash(e, 'error')
            return redirect(url_for('contact'))

        msg = ContactMessage(
            full_name=full_name, email=email,
            subject=subject, message=message,
            ip_address=request.remote_addr
        )
        db.session.add(msg)
        db.session.commit()
        flash('Message received. Our team will respond shortly.', 'success')
        return redirect(url_for('contact'))

    return render_template('contact.html')

# ── Labs listing ──
@app.route('/labs')
def labs():
    category = request.args.get('category', 'all')
    page     = request.args.get('page', 1, type=int)
    per_page = 9

    query = Lab.query.filter_by(is_active=True).order_by(Lab.created_at.desc())
    if category and category != 'all':
        query = query.filter_by(category=category)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    labs_list  = _enrich_labs(pagination.items)

    live_event = LiveEvent.query.filter(
        LiveEvent.is_active == True,
        LiveEvent.ends_at > datetime.utcnow()
    ).order_by(LiveEvent.ends_at.asc()).first()

    return render_template(
        'labs.html',
        labs        = labs_list,
        pagination  = pagination,
        active_filter = category,
        live_event  = live_event,
        stats       = _labs_stats(),
    )

# ── Launch / deploy a lab ──
@app.route('/labs/<int:lab_id>/launch')
@login_required
def launch_lab(lab_id):
    lab = Lab.query.get_or_404(lab_id)

    progress = LabProgress.query.filter_by(
        user_id=session['user_id'], lab_id=lab_id
    ).first()

    if not progress:
        progress = LabProgress(
            user_id    = session['user_id'],
            lab_id     = lab_id,
            percent    = 0,
            completed  = False,
            xp_awarded = 0,
        )
        db.session.add(progress)
        db.session.commit()
        flash(f'Lab "{lab.title}" deployed. Good luck, Operator.', 'success')
    else:
        flash(f'Resuming "{lab.title}".', 'info')

    if lab.env_url:
        return redirect(lab.env_url)
    return redirect(url_for('labs'))

# ── Join live event ──
@app.route('/labs/event/<int:event_id>/join')
@login_required
def join_event(event_id):
    event = LiveEvent.query.get_or_404(event_id)

    if not event.is_active or event.ends_at <= datetime.utcnow():
        flash('This event has already ended.', 'error')
        return redirect(url_for('labs'))

    if session['user_id'] not in [u.id for u in event.participants]:
        user = User.query.get(session['user_id'])
        event.participants.append(user)
        db.session.commit()
        flash(f'Joined "{event.title}"! {event.xp_pool:,} XP up for grabs.', 'success')
    else:
        flash('You are already enrolled in this event.', 'info')

    return redirect(url_for('labs'))

# ── Event briefing ──
@app.route('/labs/event/<int:event_id>/briefing')
def event_briefing(event_id):
    event = LiveEvent.query.get_or_404(event_id)
    return render_template('labs_briefing.html', event=event)

# ── Admin: create lab ──
@app.route('/admin/labs/create', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_create_lab():
    if request.method == 'POST':
        title       = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        category    = request.form.get('category', '').strip()
        difficulty  = request.form.get('difficulty', 'novice').strip()
        xp          = request.form.get('xp', 500, type=int)
        duration    = request.form.get('duration', 60, type=int)
        tags_raw    = request.form.get('tags', '')
        icon        = request.form.get('icon', '⚙').strip()
        env_url     = request.form.get('env_url', '').strip() or None

        if not title or not description or not category:
            flash('Title, description, and category are required.', 'error')
            return redirect(url_for('admin_create_lab'))

        tags = [t.strip() for t in tags_raw.split(',') if t.strip()]
        lab  = Lab(
            title=title, description=description, category=category,
            difficulty=difficulty, xp=xp, duration=duration,
            icon=icon, env_url=env_url, is_active=True,
        )
        lab.tags = tags
        db.session.add(lab)
        db.session.commit()
        flash(f'Lab "{title}" created.', 'success')
        return redirect(url_for('labs'))

    return render_template('lab_form.html')

# ── Admin: delete (deactivate) lab ──
@app.route('/admin/labs/<int:lab_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_lab(lab_id):
    lab = Lab.query.get_or_404(lab_id)
    lab.is_active = False
    db.session.commit()
    flash(f'Lab "{lab.title}" deactivated.', 'success')
    return redirect(url_for('labs'))

# ── Admin: create live event ──
@app.route('/admin/labs/event/create', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_create_event():
    if request.method == 'POST':
        title       = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        xp_pool     = request.form.get('xp_pool', 25000, type=int)
        ends_at_str = request.form.get('ends_at', '').strip()

        if not title or not ends_at_str:
            flash('Title and end date are required.', 'error')
            return redirect(url_for('admin_create_event'))

        try:
            ends_at = datetime.fromisoformat(ends_at_str)
        except ValueError:
            flash('Invalid date. Use YYYY-MM-DDTHH:MM format.', 'error')
            return redirect(url_for('admin_create_event'))

        event = LiveEvent(
            title=title, description=description,
            xp_pool=xp_pool, ends_at=ends_at, is_active=True,
        )
        db.session.add(event)
        db.session.commit()
        flash(f'Live event "{title}" created.', 'success')
        return redirect(url_for('labs'))

    return render_template('event_form.html')

# ── Courses listing ──
@app.route('/courses')
def courses():
    q      = request.args.get('q', '').strip()
    level  = request.args.get('level', '').strip()
    topic  = request.args.get('topic', '').strip()
    page   = request.args.get('page', 1, type=int)
    per_page = 9

    query = Course.query

    if q:
        like = f'%{q}%'
        query = query.filter(
            db.or_(Course.title.ilike(like), Course.description.ilike(like))
        )
    if level:
        query = query.filter_by(level=level)
    if topic:
        query = query.filter_by(topic=topic)

    query = query.order_by(Course.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # Add enrollment_count to each course object on-the-fly
    for course in pagination.items:
        course.enrollment_count = Enrollment.query.filter_by(course_id=course.id).count()

    return render_template(
        'training.html',
        courses      = pagination.items,
        pagination   = pagination,
        enrolled_map = _enrolled_map(),
        stats        = _course_stats(),
    )

# ── Course detail (placeholder — customise as needed) ──
@app.route('/courses/<int:course_id>')
def course_detail(course_id):
    course     = Course.query.get_or_404(course_id)
    enrollment = None
    if 'user_id' in session and session.get('user_role') == 'student':
        enrollment = Enrollment.query.filter_by(
            user_id=session['user_id'], course_id=course_id
        ).first()
    return render_template('course_detail.html', course=course, enrollment=enrollment)

# ── Enroll in a course ──
@app.route('/courses/<int:course_id>/enroll', methods=['POST'])
@login_required
def enroll_course(course_id):
    if session.get('user_role') == 'admin':
        flash('Admins cannot enroll in courses.', 'error')
        return redirect(url_for('courses'))

    course = Course.query.get_or_404(course_id)

    existing = Enrollment.query.filter_by(
        user_id=session['user_id'], course_id=course_id
    ).first()

    if existing:
        flash(f'You are already enrolled in "{course.title}".', 'info')
        return redirect(url_for('courses'))

    enrollment = Enrollment(
        user_id   = session['user_id'],
        course_id = course_id,
        progress  = 0,
    )
    db.session.add(enrollment)
    db.session.commit()
    flash(f'Enrolled in "{course.title}". Mission accepted.', 'success')
    return redirect(url_for('courses'))

# ── Update course progress (called from course detail / lesson pages) ──
@app.route('/courses/<int:course_id>/progress', methods=['POST'])
@login_required
def update_progress(course_id):
    if session.get('user_role') == 'admin':
        return redirect(url_for('courses'))

    enrollment = Enrollment.query.filter_by(
        user_id=session['user_id'], course_id=course_id
    ).first_or_404()

    new_progress = request.form.get('progress', type=int)
    if new_progress is not None and 0 <= new_progress <= 100:
        enrollment.progress    = new_progress
        enrollment.last_active = datetime.utcnow()
        db.session.commit()

    return redirect(url_for('course_detail', course_id=course_id))

# ── Admin: create course ──
@app.route('/admin/courses/create', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_create_course():
    if request.method == 'POST':
        title       = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        level       = request.form.get('level', 'Beginner').strip()
        duration    = request.form.get('duration', '').strip()
        modules     = request.form.get('modules', 0, type=int)
        topic       = request.form.get('topic', '').strip()
        image_url   = request.form.get('image_url', '').strip() or None

        if not title or not description:
            flash('Title and description are required.', 'error')
            return redirect(url_for('admin_create_course'))

        course = Course(
            title=title, description=description,
            level=level, duration=duration,
            modules=modules, topic=topic, image_url=image_url,
        )
        db.session.add(course)
        db.session.commit()
        flash(f'Course "{title}" created.', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('course_form.html')

# ── Admin: edit course ──
@app.route('/admin/courses/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_course(course_id):
    course = Course.query.get_or_404(course_id)

    if request.method == 'POST':
        course.title       = request.form.get('title', course.title).strip()
        course.description = request.form.get('description', course.description).strip()
        course.level       = request.form.get('level', course.level).strip()
        course.duration    = request.form.get('duration', course.duration).strip()
        course.modules     = request.form.get('modules', course.modules, type=int)
        course.topic       = request.form.get('topic', course.topic).strip()
        course.image_url   = request.form.get('image_url', '').strip() or None
        db.session.commit()
        flash(f'Course "{course.title}" updated.', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('course_form.html', course=course)

# ── Admin: delete course ──
@app.route('/admin/courses/<int:course_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    flash(f'Course "{course.title}" deleted.', 'success')
    return redirect(url_for('admin_dashboard'))

# ── Admin: All students page ──
@app.route('/admin/students')
@login_required
@admin_required
def admin_students():
    page     = request.args.get('page', 1, type=int)
    per_page = 25

    pagination = User.query.filter_by(role='student') \
        .order_by(User.created_at.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)

    total_students   = User.query.filter_by(role='student').count()
    active_students  = User.query.filter_by(role='student', is_active=True).count()
    total_enrollments = Enrollment.query.count()
    unread_count     = ContactMessage.query.filter_by(is_read=False).count()

    return render_template('admin_students.html',
        users             = pagination.items,
        pagination        = pagination,
        total_students    = total_students,
        active_students   = active_students,
        total_enrollments = total_enrollments,
        unread_count      = unread_count,
    )

# ── Admin: edit lab ──
@app.route('/admin/labs/<int:lab_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_lab(lab_id):
    lab = Lab.query.get_or_404(lab_id)

    if request.method == 'POST':
        lab.title       = request.form.get('title', lab.title).strip()
        lab.description = request.form.get('description', lab.description).strip()
        lab.category    = request.form.get('category', lab.category).strip()
        lab.difficulty  = request.form.get('difficulty', lab.difficulty).strip()
        lab.xp          = request.form.get('xp', lab.xp, type=int)
        lab.duration    = request.form.get('duration', lab.duration, type=int)
        lab.icon        = request.form.get('icon', lab.icon).strip()
        lab.env_url     = request.form.get('env_url', '').strip() or None
        tags_raw        = request.form.get('tags', '')
        lab.tags        = [t.strip() for t in tags_raw.split(',') if t.strip()]
        db.session.commit()
        flash(f'Lab "{lab.title}" updated.', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('lab_form.html', lab=lab)

# ── Admin: edit live event ──
@app.route('/admin/labs/event/<int:event_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_event(event_id):
    event = LiveEvent.query.get_or_404(event_id)

    if request.method == 'POST':
        event.title       = request.form.get('title', event.title).strip()
        event.description = request.form.get('description', event.description).strip()
        event.xp_pool     = request.form.get('xp_pool', event.xp_pool, type=int)
        ends_at_str       = request.form.get('ends_at', '').strip()

        if ends_at_str:
            try:
                event.ends_at = datetime.fromisoformat(ends_at_str)
            except ValueError:
                flash('Invalid date format. Use YYYY-MM-DDTHH:MM.', 'error')
                return redirect(url_for('admin_edit_event', event_id=event_id))

        db.session.commit()
        flash(f'Event "{event.title}" updated.', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('event_form.html', event=event)

# ── Admin: delete live event ──
@app.route('/admin/labs/event/<int:event_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_event(event_id):
    event = LiveEvent.query.get_or_404(event_id)
    event.is_active = False
    db.session.commit()
    flash(f'Event "{event.title}" ended.', 'success')
    return redirect(url_for('admin_dashboard'))

# ── Admin: delete message ──
# Add this route to your app.py alongside the other admin routes

@app.route('/admin/messages/<int:msg_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_message(msg_id):
    msg = ContactMessage.query.get_or_404(msg_id)
    db.session.delete(msg)
    db.session.commit()
    flash('Message deleted.', 'success')
    return redirect(url_for('admin_messages'))

if __name__ == '__main__':
    app.run(debug=True)