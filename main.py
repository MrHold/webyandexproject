from flask import Flask
from flask import render_template, redirect, request, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
import os

app = Flask(__name__)


@app.route('/', methods=['POST', 'GET'])
def photo():
    return render_template("templates/index.html")


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
