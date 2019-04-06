
import os
# import re
# import markdown
import argparse

from functools import wraps

# from flask import (Flask, render_template, flash, redirect, url_for, request,
#                    abort)
from flask import (Flask, render_template, flash, redirect, url_for, request)
from flask import jsonify
from flask import current_app

from flask_wtf import FlaskForm
from wtforms import (BooleanField, TextField, TextAreaField, PasswordField)
from wtforms.validators import (InputRequired, ValidationError)

from flask_login import (LoginManager, login_required, current_user,
                             login_user, logout_user)


# from flask import Blueprint


from wiki import Wiki
from wiki import Processors
from users import UserManager

__VERSION__ = '0.0.1'


"""
    Application Setup
    ~~~~~~~~~
"""

# parser = argparse.ArgumentParser(description='FlaskWiki')
# parser.add_argument('-p', '--port', type=int, default=8000, help='Port')
# parser.add_argument('-dir', '--directory', type=str, default='content', help='Content directory')
# parser.add_argument('-d', '--debug', action='store_true', help='Debug mode')
# parser.add_argument('-v', '--verbose', action='store_true', help='Verbose mode')
# parser.add_argument('-V', '--version', action='store_true', help='Print version and exit')
# parser.add_argument('-a', '--authentication_method', type=str, default='cleartext', help='Default authentication method')
# options = parser.parse_args()

# if options.version:
#     print('FlaskWiki-{0}'.format(__VERSION__))
#     exit()

app = Flask(__name__)

# mux = Blueprint('default', __name__)
# app.register_blueprint(mux)

# set default config items
app.config['DEBUG'] = True
app.config['CONTENT_DIR'] = 'content'
# app.config['DEBUG'] = options.debug
# app.config['CONTENT_DIR'] = options.directory
app.config['TITLE'] = 'wiki'
# app.config['AUTHENTICATION_METHOD'] = options.authentication_method
app.config['AUTHENTICATION_METHOD'] = 'cleartext'
app.config['SEARCH_IGNORE_CASE'] = True


try:
    app.config.from_pyfile(
        os.path.join(app.config.get('CONTENT_DIR'), 'config.py')
    )
except IOError:
    print ("Startup Failure: You need to place a "
           "config.py in your content directory.")


wiki = Wiki(app.config.get('CONTENT_DIR'))
users = UserManager(app.config.get('CONTENT_DIR'))

users.add_user('admin', 'dev', authentication_method=app.config.get('AUTHENTICATION_METHOD'))


loginmanager = LoginManager()
loginmanager.init_app(app)
loginmanager.login_view = 'user_login'





"""
    Forms
    ~~~~~
"""

# https://stackoverflow.com/questions/13585663/flask-wtfform-flash-does-not-display-errors
def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Error in the %s field - %s" % (
                getattr(form, field).label.text,
                error
            ), 'error')


class URLForm(FlaskForm):
    url = TextField('', [InputRequired()])

    def validate_url(form, field):
        if wiki.exists(field.data):
            raise ValidationError('The URL "%s" exists already.' % field.data)

    def clean_url(self, url):
        return Processors().clean_url(url)


class SearchForm(FlaskForm):
    term = TextField('', [InputRequired()])
    ignore_case = BooleanField(description='Ignore Case', default=app.config.get('SEARCH_IGNORE_CASE'))


class EditorForm(FlaskForm):
    title = TextField('', [InputRequired()])
    body = TextAreaField('', [InputRequired()])
    tags = TextField('')


class LoginForm(FlaskForm):
    name = TextField('', [InputRequired()])
    password = PasswordField('', [InputRequired()])

    def validate_name(form, field):
        user = users.get_user(field.data)
        if not user:
            raise ValidationError('This username does not exist.')

    def validate_password(form, field):
        user = users.get_user(form.name.data)
        if not user:
            return
        # if not user.check_password(field.data, current_app.config.get('AUTHENTICATION_METHOD')):
        if not user.check_password(field.data):
            raise ValidationError('Username and password do not match.')

class CreateUserForm(FlaskForm):
    name = TextField('', [InputRequired()])
    password = PasswordField('', [InputRequired()])

    def validate_name(form, field):
        user = users.get_user(field.data)
        if user:
            raise ValidationError('This username already exists.')


@loginmanager.user_loader
def load_user(name):
    return users.get_user(name)



def protect(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if app.config.get('PRIVATE') and not current_user.is_authenticated:
            return loginmanager.unauthorized()
        return f(*args, **kwargs)
    return wrapper



"""
    Routes
    ~~~~~~
"""

# mux = Blueprint('mux', __name__)

@app.route('/')
@protect
def home():
    page = wiki.get('home')
    if page:
        return display('home')
    return render_template('home.html')


@app.route('/index/')
@protect
def index():
    pages = wiki.index()
    return render_template('index.html', pages=pages)


@app.route('/<path:url>/')
@protect
def display(url):
    page = wiki.get_or_404(url)
    return render_template('page.html', page=page)


@app.route('/create/', methods=['GET', 'POST'])
@protect
def create():
    form = URLForm()
    if form.validate_on_submit():
        return redirect(url_for('edit', url=form.clean_url(form.url.data)))
    return render_template('create.html', form=form)


@app.route('/edit/<path:url>/', methods=['GET', 'POST'])
@protect
def edit(url):
    page = wiki.get(url)
    form = EditorForm(obj=page)
    if form.validate_on_submit():
        if not page:
            page = wiki.get_bare(url)
        form.populate_obj(page)
        page.save()
        flash('"%s" was saved.' % page.title, 'success')
        return redirect(url_for('display', url=url))
    return render_template('editor.html', form=form, page=page)


# @app.route('/preview/', methods=['POST'])
# @protect
# def preview():
#     a = request.form
#     data = {}
#     processed = Processors(a['body'])
#     data['html'], data['body'], data['meta'] = processed.out()
#     return data['html']


@app.route('/move/<path:url>/', methods=['GET', 'POST'])
@protect
def move(url):
    page = wiki.get_or_404(url)
    form = URLForm(obj=page)
    if form.validate_on_submit():
        newurl = form.url.data
        wiki.move(url, newurl)
        return redirect(url_for('display', url=newurl))
    return render_template('move.html', form=form, page=page)


@app.route('/delete/<path:url>/', methods=['GET','DELETE'])
@protect
def delete(url):
    # if 'GET' == request.method:
    page = wiki.get_or_404(url)
    wiki.delete(url)
    return jsonify({"status":"ok"})
    # flash('Page "%s" was deleted.' % page.title, 'success')
    # return redirect(url_for('home'))


@app.route('/tags/')
@protect
def tags():
    tags = wiki.get_tags()
    return render_template('tags.html', tags=tags)


@app.route('/tag/<string:name>/')
@protect
def tag(name):
    tagged = wiki.index_by_tag(name)
    return render_template('tag.html', pages=tagged, tag=name)


@app.route('/search/', methods=['GET', 'POST'])
@protect
def search():
    form = SearchForm()
    if form.validate_on_submit():
        results = wiki.search(form.term.data, form.ignore_case.data)
        return render_template('search.html', form=form,
                               results=results, search=form.term.data)
    return render_template('search.html', form=form, search=None)


@app.route('/user/login/', methods=['GET', 'POST'])
def user_login():
    form = LoginForm()
    if form.validate_on_submit():
        user = users.get_user(form.name.data)
        login_user(user)
        user.set('authenticated', True)
        flash('Login successful.', 'success')
        return redirect(request.args.get("next") or url_for('index'))
    return render_template('login.html', form=form)


@app.route('/user/logout/')
@login_required
def user_logout():
    current_user.set('authenticated', False)
    logout_user()
    flash('Logout successful.', 'success')
    return redirect(url_for('index'))


@app.route('/user/')
def user_index():
    pass


@app.route('/user/create/', methods=['GET', 'POST'])
def user_create():
    # TODO
    #  - show validation error?
    form = CreateUserForm()
    if form.validate_on_submit():
        user = users.add_user(form.name.data, form.password.data,
                                authentication_method=app.config.get('AUTHENTICATION_METHOD'))
        flash('User created.', 'success')
        return redirect(request.args.get("next") or url_for('user_login'))
    else:
        flash_errors(form)
    return render_template('create_user.html', form=form)


@app.route('/user/<int:user_id>/')
def user_admin(user_id):
    pass


@app.route('/user/delete/<int:user_id>/')
def user_delete(user_id):
    pass


"""
    Error Handlers
    ~~~~~~~~~~~~~~
"""


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404



if __name__ == '__main__':
    # app.register_blueprint(mux)
    app.run(
        host = '0.0.0.0',
        # port = options.port
        port = app.config.get('PORT', 8000)
    )
