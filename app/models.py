from . import db
from datetime import datetime

class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    emails = db.relationship('Email', backref='campaign', lazy=True)

class Email(db.Model):
    id = db.Column(db.String(36), primary_key=True)  # Using UUIDs for email IDs
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    recipient = db.Column(db.String(255), nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    opens = db.relationship('Open', backref='email', lazy=True)
    clicks = db.relationship('Click', backref='email', lazy=True)

class Open(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.String(36), db.ForeignKey('email.id'), nullable=False)
    opened_at = db.Column(db.DateTime, default=datetime.utcnow)

class Click(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.String(36), db.ForeignKey('email.id'), nullable=False)
    url = db.Column(db.String(2048), nullable=False)
    clicked_at = db.Column(db.DateTime, default=datetime.utcnow)
