import pandas as pd
import csv
import gunicorn
from os import environ
from functools import wraps
from flask import Flask, abort, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from flask_login import login_user, UserMixin, LoginManager, current_user, logout_user, login_required
from wtforms import StringField, SubmitField, URLField, SelectField
from flask_ckeditor import CKEditor, CKEditorField
from wtforms.validators import DataRequired, URL

app = Flask(__name__)
app.config['SECRET_KEY'] = '123'
bootstrap = Bootstrap5(app)
ckeditor = CKEditor(app)

login_manager = LoginManager()
login_manager.init_app(app)


class CafeForm(FlaskForm):
    cafe = StringField("Кав'ярня", validators=[DataRequired()])
    review = CKEditorField('Відгук', validators=[DataRequired()])
    map_link = URLField('Посилання на Гугл Карти', validators=[DataRequired()])
    submit = SubmitField('Добре')


class Admin(UserMixin):
    def __init__(self):
        self.id = 1

    def get_id(self):
        return self.id


get_cafes = lambda: pd.read_csv('./static/cafes.csv', sep='|')

admin = Admin()
cafes = get_cafes()


def download_cafes():
    global cafes
    cafes = get_cafes()


def upload_cafes():
    global cafes
    cafes.to_csv('./static/cafes.csv', sep='|', index=False)


@login_manager.user_loader
def load_user(id=1):
    return admin


def admin_only(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_user.is_authenticated:
            return func(*args, **kwargs)
        else:
            return abort(403)

    return wrapper


@app.route('/')
def home():
    download_cafes()
    return render_template('index.html', cafes=cafes.reset_index().to_dict(orient='records'))


@app.route('/admin')
def login_admin():
    if request.args.get('p') == environ['ADMIN_PSWD']:
        login_user(admin)
    return redirect(url_for('home'))


@app.route('/exit')
@admin_only
def exit_admin():
    logout_user()
    return redirect(url_for('home'))


@app.route("/delete/<int:cafe_idx>")
@admin_only
def delete_cafe(cafe_idx: int):
    global cafes
    cafes = cafes.drop([cafe_idx])
    upload_cafes()
    return redirect(url_for('home'))


@app.route("/edit/<int:cafe_idx>", methods=['GET', 'POST'])
@admin_only
def edit_cafe(cafe_idx: int):
    cafe_form = CafeForm(**cafes.loc[[cafe_idx]].to_dict(orient='records')[0])
    if cafe_form.validate_on_submit():
        new_data = cafe_form.data
        del new_data['csrf_token']
        del new_data['submit']
        cafes.loc[[cafe_idx], list(new_data.keys())] = list(new_data.values())
        upload_cafes()
        return redirect(url_for('home'))
    return render_template('cafe.html', cafe_form=cafe_form)


@app.route('/add_cafe', methods=['GET', 'POST'])
@admin_only
def add_cafe():
    global cafes
    cafe_form = CafeForm()
    if cafe_form.validate_on_submit():
        new_data = cafe_form.data
        del new_data['csrf_token']
        del new_data['submit']
        cafes.loc[len(cafes)] = new_data
        upload_cafes()
        return redirect(url_for('home'))
    return render_template('cafe.html', cafe_form=cafe_form)


if __name__ == '__main__':
    app.run(debug=True)
