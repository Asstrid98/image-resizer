from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class ImageJob(db.Model):
    __tablename__ = 'image_jobs'

    id = db.Column(db.Integer, primary_key=True)
    original_filename = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default='pending')
    width = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Integer, nullable=False)
    original_size = db.Column(db.Integer)
    resized_size = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    error_message = db.Column(db.String(500), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'original_filename': self.original_filename,
            'status': self.status,
            'width': self.width,
            'height': self.height,
            'original_size': self.original_size,
            'resized_size': self.resized_size,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message
        }