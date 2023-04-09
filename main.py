from flask import Flask
from flask import render_template, redirect, request, url_for, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import json
from flask_wtf import FlaskForm
from data.users import User
from data import db_session
from forms.user import RegisterForm, LoginForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
import os
import requests
import pymorphy3
import logging

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['RECAPTCHA_PUBLIC_KEY'] = '6LdOeXIlAAAAAAg2kEZ9uockHFNLJurPcT82qeN_'
app.config['RECAPTCHA_PRIVATE_KEY'] = '6LdOeXIlAAAAAPASxPhAQhq89k7yA7UIT1u5XRzy'

@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")

morph = pymorphy3.MorphAnalyzer()
answer = {
    "Слово": "",
    "Начальная форма": "",
    "Граммемы": ""
}

def check_word(word):
    req = 'https://speller.yandex.net/services/spellservice.json/checkTexts?text=' + str(word)
    response = requests.get(req)
    if response:
        json_response = response.json()
        if json_response and json_response != [[]]:
            return json_response[0][0]["s"]
    else:
        print('Ошибка выполнения запроса')

@app.route('/', methods=['POST', 'GET'])
def main():
    db_sess = db_session.create_session()
    if request.method == "GET":
        return render_template("index.html", toget=False)
    elif request.method == "POST":
        word = request.form["search"]
        if word:
            word_checked = check_word(word)
            if word_checked and type(word_checked).__name__ == 'list':
                word = word_checked[0]
        if current_user.is_authenticated:
            usr = db_sess.query(User).filter(User.id == current_user.id).first()
            if usr.words:
                usr.words = usr.words + ', ' + word
            else:
                usr.words = word
            db_sess.commit()
        answer["Слово"] = str(morph.parse(word)[0].word)
        answer["Начальная форма"] = morph.parse(word)[0].normal_form
        answer["Граммемы"] = morph.parse(word)[0].tag.cyr_repr
        json_answer = json.dumps(answer, ensure_ascii=False)

        return render_template("index.html", toget=True, answer=answer)

@app.route('/user')
@login_required
def user_page():
    db_sess = db_session.create_session()
    return render_template("user.html", title=f'Профиль {current_user.username}', words=list(set(current_user.words.split(', '))))
    

@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация', form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация', form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            username=form.username.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html', message="Неправильный логин или пароль", form=form)
    return render_template('login.html', title='Авторизация', form=form)

@app.route('/about')
def about():
    return render_template('about.html', title="О проекте")

if __name__ == '__main__':
    db_session.global_init("db/users.db")
    port = int(os.environ.get("PORT", 5000))
    app.run(port=port, host='0.0.0.0', debug=False)
