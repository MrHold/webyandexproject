from flask import Flask
from flask import render_template, redirect, request, url_for, abort, Blueprint, session, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import json
from flask_wtf import FlaskForm
from data.users import User
from data.words import Word
from data import db_session
from forms.user import RegisterForm, LoginForm
from forms.word import WordGame
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
##app.config['TESTING'] = True если понадобится выключить проверку капчи

@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")

@app.route("/toggle-theme")
def toggle_theme():
    current_theme = session.get("theme")
    if current_theme == "dark":
        session["theme"] = "light"
    else:
        session["theme"] = "dark"
    # возврат на предыдущую страницу при смене темы (т.к. смена темы - как бы отдельная ссылка)
    if 'url' in session:
        return redirect(session['url'])
    else:
        return redirect('/')

morph = pymorphy3.MorphAnalyzer()
# шаблон для ответа
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
@app.route('/index', methods=['POST', 'GET'])
def main():
    # установка необходимых для игры переменных сессии и переменной с текущей страницей
    session['game_ids'] = []
    session['gamek'] = 0
    session['url'] = '/'
    db_sess = db_session.create_session()
    if request.method == "GET":
        return render_template("index.html", toget=False)
    elif request.method == "POST":
        word = request.form["search"].lower()
        word_not_correct = word
        if word:
            word_checked = check_word(word)
            if word_checked and type(word_checked).__name__ == 'list':
                word = word_checked[0]
        if current_user.is_authenticated:
            # добавление слова в список слов, которые искал пользователь
            usr = db_sess.query(User).filter(User.id == current_user.id).first()
            if usr.words:
                usr.words = usr.words + ', ' + word
            else:
                usr.words = word
        if word_not_correct != word:
            # добавление слова в список для игры
            wrd = db_sess.query(Word).filter(Word.correct == word).first()
            if wrd:
                if word_not_correct not in wrd.not_correct:
                    wrd.not_correct = wrd.not_correct + ', ' + word_not_correct.lower()
            elif not wrd:
                x = Word()
                x.correct = word.lower()
                x.not_correct = word_not_correct.lower()
                db_sess.add(x)
            db_sess.commit()
        answer["Слово"] = str(morph.parse(word)[0].word)
        answer["Начальная форма"] = morph.parse(word)[0].normal_form
        answer["Граммемы"] = morph.parse(word)[0].tag.cyr_repr
        json_answer = json.dumps(answer, ensure_ascii=False)

        return render_template("index.html", toget=True, answer=answer)

@app.route('/user/<int:id>')
@login_required
def user_page(id):
    session['url'] = f'/user/{id}'
    session['game_ids'] = []
    db_sess = db_session.create_session()
    return render_template("user.html", title=f'Профиль {current_user.username}', words=list(set(current_user.words.split(', '))))

@app.route('/game', methods=['POST', 'GET'])
@login_required
def game():
    err = ''
    form = WordGame()
    if request.method == "GET":
        session['url'] = f'/game'
        k = int(session['gamek'])
        db_sess = db_session.create_session()
        words = db_sess.query(Word).all()
        wrds = []
        for i in range(len(words)):
            # шаблон для вывода слова
            d = {'id': 0, 'correct': '', 'not_correct': ''}
            d['id'] = words[i].id
            d['correct'] = words[i].correct
            d['not_correct'] = words[i].not_correct
            wrds.append(d)
        # если игра пройдена (кончились слова)
        if k >= len(wrds):
            session['gamek'] = 0
            session['game_ids'] = []
            return render_template("game.html", message=err, title='Игра по словам', form=form, wrds=None)
        else:
            return render_template("game.html", message=err, title='Игра по словам', form=form, wrds=wrds[k])
    elif request.method == "POST":
        word = request.form.get("word").lower()
        session['url'] = f'/game'
        k = int(session['gamek'])
        db_sess = db_session.create_session()
        words = db_sess.query(Word).all()
        wrds = []
        # x - переменная со списком айди решённых слов
        x = session['game_ids']
        for i in range(len(words)):
            # шаблон для вывода слова
            d = {'id': 0, 'correct': '', 'not_correct': ''}
            d['id'] = words[i].id
            d['correct'] = words[i].correct
            if ',' in words[i].not_correct:
                d['not_correct'] = words[i].not_correct
            else:
                d['not_correct'] = words[i].not_correct
            for j in range(1, k + 1):
                if word and word == words[j].correct:
                    x.append(i)
            wrds.append(d)
        # предупреждения \/
        if word == words[k].correct:
            k +=1
            session['gamek'] += 1
            err = 'Правильно. Обновите страницу.'
        else:
            err = 'Неправильно. Попробуйте снова.'
        session['game_ids'] = x
        # если игра пройдена (кончились слова)
        if k >= len(wrds):
            session['gamek'] = 0
            session['game_ids'] = []
            return render_template("game.html", message=err, title='Игра по словам', form=form, wrds=None)
        else:
            return render_template("game.html", message=err, title='Игра по словам', form=form, wrds=wrds[k])

@app.route('/register', methods=['GET', 'POST'])
def reqister():
    session['game_ids'] = []
    session['gamek'] = 0
    session['url'] = '/register'
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
    session['game_ids'] = []
    session['gamek'] = 0
    session['url'] = '/login'
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
    session['game_ids'] = []
    session['gamek'] = 0
    session['url'] = '/about'
    return render_template('about.html', title="О проекте")

if __name__ == '__main__':
    db_session.global_init("db/users.db")
    port = int(os.environ.get("PORT", 5000))
    app.run(port=port, host='0.0.0.0', debug=False)
