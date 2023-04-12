import datetime
import sqlalchemy
from flask_login import UserMixin
from sqlalchemy import orm
from werkzeug.security import generate_password_hash, check_password_hash

from .db_session import SqlAlchemyBase


class Word(SqlAlchemyBase, UserMixin):
    __tablename__ = 'words'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    not_correct = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    correct = sqlalchemy.Column(sqlalchemy.String, unique=True, nullable=True)

    def __repr__(self):
        return f'<Word> {self.id} {self.word_not_correct} {self.word_correct}'
