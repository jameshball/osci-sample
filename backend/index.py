import functools
import json
import os
import re

from flask import Flask, request, redirect, abort, render_template, url_for
from flask_migrate import Migrate
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from oauthlib.oauth2 import WebApplicationClient
import requests

from backend.sample import sample, get_samples
from backend.member import member
from backend.model import db

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

ALLOWED_EXTENSIONS = {'wav'}

class ReverseProxied(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        scheme = environ.get('HTTP_X_FORWARDED_PROTO')
        if scheme:
            environ['wsgi.url_scheme'] = scheme
        return self.app(environ, start_response)

app = Flask(__name__, template_folder="../templates", static_folder="../static")
app.wsgi_app = ReverseProxied(app.wsgi_app)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)
app.register_blueprint(member)
app.register_blueprint(sample)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.session_protection = None

app.config['MAX_CONTENT_LENGTH'] = 21 * 1024 * 1024
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

if 'DATABASE_URL' in os.environ:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL'].replace("postgres://", "postgresql://", 1)

db.app = app
db.init_app(app)
from backend.model import *

migrate = Migrate(app, db)

client = WebApplicationClient(GOOGLE_CLIENT_ID)


@login_manager.user_loader
def load_user(user_id):
    return Member.query.filter_by(google_id=user_id).first()


def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()


@app.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('index.html', samples=get_samples())
    else:
        return render_template('login.html')


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/new_sample', methods=['GET', 'POST'])
@login_required
def new_sample():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if not allowed_file(file.filename):
            return redirect(request.url)

        anonymous = request.form.get('anonymous', 'off')
        description = request.form.get('description', '')

        sample = Sample()
        sample.audio_data = file.read()
        sample.name = file.filename
        sample.creator = current_user.id
        sample.sample_rate = 192000
        sample.bit_depth = 32
        sample.description = description
        sample.num_downloads = 0
        sample.anonymous = True if anonymous == 'on' else False

        db.session.add(sample)
        db.session.commit()

        return redirect(url_for('index', _scheme='https', _external=True))

    return render_template('new_sample.html', first_name=current_user.first_name, last_name=current_user.last_name)


@app.route("/login")
def login():
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    base_url = re.sub("^http:", "https:", request.base_url, 1)

    print(base_url)

    # Prepare request to get access to specified Google data scopes
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)


@app.route("/login/callback")
def callback():
    # Get authorization code sent by Google
    code = request.args.get("code")

    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send a request to get tokens
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    client.parse_request_body_response(json.dumps(token_response.json()))

    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        user_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        given_name = userinfo_response.json()["given_name"]
        family_name = userinfo_response.json()["family_name"]
    else:
        return "User email not available or not verified by Google.", 400

    mem = Member()
    mem.google_id = unique_id
    mem.first_name = given_name
    mem.last_name = family_name
    mem.email = user_email
    mem.profile_pic = picture

    # If the member hasn't already been made, add it to db
    if not Member.query.filter(Member.google_id == unique_id).first():
        db.session.add(mem)
        db.session.commit()

    login_user(mem, remember=True)

    return redirect(url_for('index', _scheme='https', _external=True))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index', _scheme='https', _external=True))


@app.route("/auth-test")
def auth_test():
    if current_user.is_authenticated:
        return 'Authenticated!'
    else:
        return 'Not authenticated!'


if __name__ == '__main__':
    app.run(ssl_context='adhoc')
