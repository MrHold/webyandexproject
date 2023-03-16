from flask import Flask
from flask import render_template, redirect, request, url_for
import json
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
import os
import pymorphy3

app = Flask(__name__)

morph = pymorphy3.MorphAnalyzer()
answer = {
    "Слово": "",
    "Начальная форма": "",
    "Граммемы": "",
    "Ударение": ""
}

@app.route('/', methods=['POST', 'GET'])
def main():
    if request.method == "GET":
        return render_template("index.html")
    elif request.method == "POST":
        word = request.form["search"]
        answer["Слово"] = morph.parse(word)[0].word
        answer["Начальная форма"] = morph.parse(word)[0].normal_form
        answer["Граммемы"] = morph.parse(word)[0].tag.cyr_repr
        print(morph.parse(word)[0])
        json_answer = json.dumps(answer, ensure_ascii=False)

        return render_template("index.html", answer=answer)


if __name__ == '__main__':
    app.debug = True
    app.run(port=8080, host='127.0.0.1')
