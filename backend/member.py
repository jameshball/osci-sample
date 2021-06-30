from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required

from backend.model import db, Member

member = Blueprint('member', __name__)


@member.route('/member', methods=['GET'])
@login_required
def get_member():
    u = current_user
    return jsonify(
        first_name=u.first_name,
        last_name=u.last_name,
    )
