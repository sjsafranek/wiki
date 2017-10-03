"""
    User classes & helpers
    ~~~~~~~~~~~~~~~~~~~~~~
"""
import os
import json
import binascii
import hashlib
from functools import wraps

from flask import current_app
from flask_login import current_user



class UserManager(object):
    """A very simple user Manager, that saves it's data as json."""
    def __init__(self, path):
        self.file = os.path.join(path, 'users.json')

    def read(self):
        if not os.path.exists(self.file):
            return {}
        with open(self.file) as f:
            data = json.loads(f.read())
        return data

    def write(self, data):
        with open(self.file, 'w') as f:
            f.write(json.dumps(data, indent=2))

    def add_user(self, name, password,
                 active=True, roles=[], authentication_method=None):
        users = self.read()
        if users.get(name):
            return False
        if authentication_method is None:
            authentication_method = get_default_authentication_method()
        new_user = {
            'active': active,
            'roles': roles,
            'authentication_method': authentication_method,
            'authenticated': False
        }
        # Currently we have only two authentication_methods: cleartext and
        # hash. If we get more authentication_methods, we will need to go to a
        # strategy object pattern that operates on User.data.
        if authentication_method == 'hash':
            new_user['hash'] = make_salted_hash(password)
        elif authentication_method == 'cleartext':
            new_user['password'] = password
        else:
            raise NotImplementedError(authentication_method)
        users[name] = new_user
        self.write(users)
        userdata = users.get(name)
        return User(self, name, userdata)

    def get_user(self, name):
        users = self.read()
        userdata = users.get(name)
        if not userdata:
            return None
        return User(self, name, userdata)

    def delete_user(self, name):
        users = self.read()
        if not users.pop(name, False):
            return False
        self.write(users)
        return True

    def update(self, name, userdata):
        data = self.read()
        data[name] = userdata
        self.write(data)


class User(object):
    def __init__(self, manager, name, data):
        self.manager = manager
        self.name = name
        self.data = data

    def get(self, option):
        return self.data.get(option)

    def set(self, option, value):
        self.data[option] = value
        self.save()

    def save(self):
        self.manager.update(self.name, self.data)

    def is_authenticated(self):
        return self.data.get('authenticated')

    def is_active(self):
        return self.data.get('active')

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.name

    def check_password(self, password):
        """Return True, return False, or raise NotImplementedError if the
        authentication_method is missing or unknown."""
        authentication_method = self.data.get('authentication_method', None)
        if authentication_method is None:
            authentication_method = get_default_authentication_method()
        # See comment in UserManager.add_user about authentication_method.
        if authentication_method == 'hash':
            result = check_hashed_password(password, self.get('hash'))
        elif authentication_method == 'cleartext':
            result = (self.get('password') == password)
        else:
            raise NotImplementedError(authentication_method)
        return result


def get_default_authentication_method():
    return current_app.config.get('DEFAULT_AUTHENTICATION_METHOD', 'cleartext')



# TODO
#  - Move to User Model
def make_salted_hash(password, salt=None):
    return setPassword(password, salt)

def check_hashed_password(password, salted_hash):
    return isPassword(password, salted_hash)

def _salt(algo):
    import random
    string1 = str(random.random()).encode('utf-8')
    string2 = str(random.random()).encode('utf-8')
    salt = hashlib.new(algo)
    salt.update(string1)
    salt.update(string2)
    return salt.hexdigest()[:5]

def _hash(algo, salt, string_to_encrypt):
    hsh  = hashlib.new(algo)
    hsh.update(salt.encode('utf-8'))
    hsh.update(string_to_encrypt.encode('utf-8'))
    return hsh.hexdigest()

def setPassword(password, salt):
    import random
    algo = "sha256"
    if not salt:
        salt = _salt(algo)
    hsh = _hash(algo, salt, password)
    password = '%s$%s$%s' % (algo, salt, hsh)
    return password

def isPassword(password, hashed_password):
    """
    Returns a boolean of whether the raw_password was correct. Handles
    encryption formats behind the scenes.
    """
    m = hashlib.sha256()
    algo, salt, hsh = hashed_password.split('$')
    check = _hash(algo, salt, password)
    return hsh == check
#.end



def protect(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if current_app.config.get('PRIVATE') and not current_user.is_authenticated():
            return current_app.login_manager.unauthorized()
        return f(*args, **kwargs)
    return wrapper
