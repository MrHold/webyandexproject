from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField, SubmitField, BooleanField
from wtforms.fields import EmailField
from wtforms.validators import DataRequired, Email, EqualTo, Length
import email_validator


class RegisterForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired(), Email(message=None, granular_message=True)])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=8, message="Пароль должен быть больше 8 символов"), EqualTo('password_again', message='Пароли должны совпадать')])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    username = StringField('Никнейм пользователя', validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')
