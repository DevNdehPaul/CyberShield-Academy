from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class ContactMessage(db.Model):
    __tablename__ = 'contact_messages'

    id         = db.Column(db.Integer, primary_key=True)
    full_name  = db.Column(db.String(120), nullable=False)
    email      = db.Column(db.String(120), nullable=False)
    subject    = db.Column(db.String(200), nullable=False)
    message    = db.Column(db.Text, nullable=False)
    ip_address = db.Column(db.String(60), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ContactMessage {self.id} — {self.full_name}>'