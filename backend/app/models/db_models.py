"""
SQLAlchemy models for the application.
"""
from datetime import datetime
import json
from sqlalchemy import Column, String, Float, DateTime, Text, Boolean

from app.database import Base

class DBTask(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String, nullable=False, default="medium")
    status = Column(String, nullable=False, default="pending")
    due_date = Column(DateTime, nullable=True)
    assigned_to = Column(String, nullable=True)
    
    # Store tags as a JSON string for SQLite simplicity
    tags_json = Column(Text, nullable=False, default="[]")
    
    source_email = Column(String, nullable=True)
    extracted_from = Column(Text, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    @property
    def tags(self):
        """Getter for tags, parses JSON string to list."""
        try:
            return json.loads(self.tags_json)
        except Exception:
            return []

    @tags.setter
    def tags(self, value):
        """Setter for tags, converts list to JSON string."""
        if value is None:
            self.tags_json = "[]"
        else:
            self.tags_json = json.dumps(value)
