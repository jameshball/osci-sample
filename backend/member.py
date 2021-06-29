from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required

from backend.model import db, Member

member = Blueprint('member', __name__)

