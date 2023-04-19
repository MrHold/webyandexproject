from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


class WordGame(FlaskForm):
    word = StringField('Введите правильную версию слова', validators=[DataRequired()])
    submit = SubmitField('Проверить')
