#
# """
#     Forms
#     ~~~~~
# """
#
#
# class URLForm(FlaskForm):
#     url = TextField('', [InputRequired()])
#
#     def validate_url(form, field):
#         if wiki.exists(field.data):
#             raise ValidationError('The URL "%s" exists already.' % field.data)
#
#     def clean_url(self, url):
#         return Processors().clean_url(url)
#
#
# class SearchForm(FlaskForm):
#     term = TextField('', [InputRequired()])
#     ignore_case = BooleanField(description='Ignore Case', default=app.config.get('SEARCH_IGNORE_CASE'))
#
#
# class EditorForm(FlaskForm):
#     title = TextField('', [InputRequired()])
#     body = TextAreaField('', [InputRequired()])
#     tags = TextField('')
#
#
# class LoginForm(FlaskForm):
#     name = TextField('', [InputRequired()])
#     password = PasswordField('', [InputRequired()])
#
#     def validate_name(form, field):
#         user = users.get_user(field.data)
#         if not user:
#             raise ValidationError('This username does not exist.')
#
#     def validate_password(form, field):
#         user = users.get_user(form.name.data)
#         if not user:
#             return
#         if not user.check_password(field.data, current_app.config.get('AUTHENTICATION_METHOD')):
#             raise ValidationError('Username and password do not match.')
#
# class CreateUserForm(FlaskForm):
#     name = TextField('', [InputRequired()])
#     password = PasswordField('', [InputRequired()])
