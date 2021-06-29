import time
from datetime import datetime

from flask import Blueprint, request, Response, abort
from flask_login import current_user, login_required

sample = Blueprint('sample', __name__)

