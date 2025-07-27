"""
Story dependency association table for the Agile Management MCP Server.
"""

from sqlalchemy import Table, Column, String, ForeignKey, CheckConstraint
from .epic import Base

story_dependencies = Table(
    'story_dependencies',
    Base.metadata,
    Column('story_id', String, ForeignKey('stories.id'), primary_key=True),
    Column('depends_on_story_id', String, ForeignKey('stories.id'), primary_key=True),
    CheckConstraint('story_id != depends_on_story_id', name='ck_no_self_dependency')
)