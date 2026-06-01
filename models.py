from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    first_name    = db.Column(db.String(80), nullable=False)
    last_name     = db.Column(db.String(80), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role          = db.Column(db.String(30), default='student')
    is_active     = db.Column(db.Boolean, default=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    enrollments   = db.relationship('Enrollment', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'


class ContactMessage(db.Model):
    __tablename__ = 'contact_messages'
    id         = db.Column(db.Integer, primary_key=True)
    full_name  = db.Column(db.String(120), nullable=False)
    email      = db.Column(db.String(120), nullable=False)
    subject    = db.Column(db.String(200), nullable=False)
    message    = db.Column(db.Text, nullable=False)
    ip_address = db.Column(db.String(60), nullable=True)
    is_read    = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Course(db.Model):
    __tablename__ = 'courses'
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    level       = db.Column(db.String(50), default='Beginner')
    duration    = db.Column(db.String(50))
    modules     = db.Column(db.Integer, default=0)
    topic       = db.Column(db.String(100), nullable=True)   # NEW
    image_url   = db.Column(db.String(512), nullable=True)   # NEW
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    enrollments = db.relationship('Enrollment', backref='course', lazy=True)

class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id   = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    progress    = db.Column(db.Integer, default=0)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)


# ── LAB MODELS ───────────────────────────────────────────────────────────────

class Lab(db.Model):
    __tablename__ = 'lab'

    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text,        nullable=False)
    category    = db.Column(db.String(60),  nullable=False, index=True)
    difficulty  = db.Column(db.String(20),  nullable=False, default='novice')
    xp          = db.Column(db.Integer,     nullable=False, default=500)
    duration    = db.Column(db.Integer,     nullable=False, default=60)
    icon        = db.Column(db.String(10),  default='⚙')
    _tags       = db.Column('tags', db.Text, default='')
    env_url     = db.Column(db.String(512), nullable=True)
    is_active   = db.Column(db.Boolean,     default=True, index=True)
    created_at  = db.Column(db.DateTime,    default=datetime.utcnow)

    progress_records = db.relationship(
        'LabProgress', backref='lab', lazy='dynamic', cascade='all, delete-orphan'
    )

    @property
    def tags(self):
        return [t.strip() for t in self._tags.split(',') if t.strip()] if self._tags else []

    @tags.setter
    def tags(self, tag_list):
        self._tags = ','.join(tag_list)

    def __repr__(self):
        return f'<Lab {self.id}: {self.title}>'


class LabProgress(db.Model):
    __tablename__ = 'lab_progress'
    __table_args__ = (db.UniqueConstraint('user_id', 'lab_id', name='uq_user_lab'),)

    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    lab_id       = db.Column(db.Integer, db.ForeignKey('lab.id'),   nullable=False, index=True)
    percent      = db.Column(db.Integer, default=0)
    completed    = db.Column(db.Boolean, default=False)
    xp_awarded   = db.Column(db.Integer, default=0)
    started_at   = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    def mark_complete(self):
        if not self.completed:
            self.percent      = 100
            self.completed    = True
            self.completed_at = datetime.utcnow()
            self.xp_awarded   = self.lab.xp

    def __repr__(self):
        return f'<LabProgress user={self.user_id} lab={self.lab_id} {self.percent}%>'


class LiveEvent(db.Model):
    __tablename__ = 'live_event'

    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text,        nullable=False)
    xp_pool     = db.Column(db.Integer,     default=25_000)
    ends_at     = db.Column(db.DateTime,    nullable=False)
    is_active   = db.Column(db.Boolean,     default=True, index=True)
    created_at  = db.Column(db.DateTime,    default=datetime.utcnow)

    participants = db.relationship(
        'User',
        secondary='event_participants',   # string ref — resolved after table is defined below
        lazy='dynamic',
        backref=db.backref('events', lazy='dynamic'),
    )

    def __repr__(self):
        return f'<LiveEvent {self.id}: {self.title}>'


# Defined AFTER both User and LiveEvent so both tables are already registered
event_participants = db.Table(
    'event_participants',
    db.Column('event_id', db.Integer, db.ForeignKey('live_event.id'), primary_key=True),
    db.Column('user_id',  db.Integer, db.ForeignKey('users.id'),      primary_key=True),
)