"""
    Routes
    ~~~~~~
"""
from flask import Blueprint
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask import send_file
from flask_login import current_user
from flask_login import login_required
from flask_login import login_user
from flask_login import logout_user

from core import Processor
from web.forms import EditorForm
from web.forms import LoginForm
from web.forms import CreateUserForm
from web.forms import SearchForm
from web.forms import URLForm
from web import current_wiki
from web import current_users
from web.user import protect

from web.utils import zipdir


bp = Blueprint('wiki', __name__)


@bp.route('/')
@protect
def home():
    page = current_wiki.get('home')
    if page:
        return display('home')
    return render_template('home.html')


@bp.route('/index/')
@protect
def index():
    pages = current_wiki.index()
    return render_template('index.html', pages=pages)


@bp.route('/<path:url>/')
@protect
def display(url):
    page = current_wiki.get_or_404(url)
    return render_template('page.html', page=page)


@bp.route('/create/', methods=['GET', 'POST'])
@login_required
@protect
def create():
    form = URLForm()
    if form.validate_on_submit():
        return redirect(url_for(
            'wiki.edit', url=form.clean_url(form.url.data)))
    return render_template('create.html', form=form)


@bp.route('/edit/<path:url>/', methods=['GET', 'POST'])
@login_required
@protect
def edit(url):
    page = current_wiki.get(url)
    form = EditorForm(obj=page)
    if form.validate_on_submit():
        if not page:
            page = current_wiki.get_bare(url)
        form.populate_obj(page)
        page.save()
        flash('"%s" was saved.' % page.title, 'success')
        return redirect(url_for('wiki.display', url=url))
    return render_template('editor.html', form=form, page=page)


@bp.route('/preview/', methods=['POST'])
@protect
def preview():
    data = {}
    processor = Processor(request.form['body'])
    data['html'], data['body'], data['meta'] = processor.process()
    return data['html']


@bp.route('/move/<path:url>/', methods=['GET', 'POST'])
@protect
def move(url):
    page = current_wiki.get_or_404(url)
    form = URLForm(obj=page)
    if form.validate_on_submit():
        newurl = form.url.data
        current_wiki.move(url, newurl)
        return redirect(url_for('wiki.display', url=newurl))
    return render_template('move.html', form=form, page=page)


@bp.route('/delete/<path:url>/')
@protect
def delete(url):
    page = current_wiki.get_or_404(url)
    current_wiki.delete(url)
    flash('Page "%s" was deleted.' % page.title, 'success')
    return redirect(url_for('wiki.home'))


@bp.route('/tags/')
@protect
def tags():
    tags = current_wiki.get_tags()
    return render_template('tags.html', tags=tags)


@bp.route('/tag/<string:name>/')
@protect
def tag(name):
    tagged = current_wiki.index_by_tag(name)
    return render_template('tag.html', pages=tagged, tag=name)


@bp.route('/search/', methods=['GET', 'POST'])
@protect
def search():
    form = SearchForm()
    if form.validate_on_submit():
        results = current_wiki.search(form.term.data, form.ignore_case.data)
        return render_template('search.html', form=form,
                               results=results, search=form.term.data)
    return render_template('search.html', form=form, search=None)

@bp.route('/login/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = current_users.get_user(form.name.data)
        login_user(user)
        user.set('authenticated', True)
        flash('Login successful.', 'success')
        return redirect(request.args.get("next") or url_for('wiki.index'))
    return render_template('login.html', form=form)


@bp.route('/logout/')
@login_required
def logout():
    current_user.set('authenticated', False)
    logout_user()
    flash('Logout successful.', 'success')
    return redirect(url_for('wiki.index'))

# @bp.route('/user/')
# def user_index():
#     pass

@bp.route('/user/create/', methods=['GET', 'POST'])
def user_create():
    form = CreateUserForm()
    if form.validate_on_submit():
        current_users.add_user(
            form.username.data,
            form.password.data,
            authentication_method='hash')
        flash('User created.', 'success')
        return redirect(request.args.get("next") or url_for('wiki.login'))
    return render_template('create_user.html', form=form)

# @bp.route('/user/<int:user_id>/')
# def user_admin(user_id):
#     pass

# @bp.route('/user/delete/<int:user_id>/')
# def user_delete(user_id):
#     pass

@bp.route('/export/')
@login_required
@protect
def export_content():
    if 'superuser' in current_user.data['roles']:
        zipArchive = zipdir('content/')
        return send_file(zipArchive, attachment_filename='content.zip', as_attachment=True)
    return render_template('error.html', error={
                'code':401,
                'message':'Unauthorized'})

"""
    Error Handlers
    ~~~~~~~~~~~~~~
"""

@bp.errorhandler(401)
def unauthorized(error):
    return render_template('401.html'), 401

@bp.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404
