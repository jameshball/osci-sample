import time
from datetime import datetime

from flask import Blueprint, request, Response, abort
from flask_login import current_user, login_required

from backend.model import db, Member, Sample

sample = Blueprint('sample', __name__)


def get_samples():
    samples = Sample.query.all()

    samples.sort(key=lambda s: s.num_downloads)

    samples_obj = []
    for sample in samples:
        creator = Member.query.get(sample.creator)

        samples_obj.append({
            'id': sample.id,
            'name': sample.name,
            'description': sample.description,
            'sample_rate': sample.sample_rate,
            'bit_depth': sample.bit_depth,
            'num_downloads': sample.num_downloads,
            'first_name': creator.first_name,
            'last_name': creator.last_name,
            'username': creator.username,
        })

    return samples_obj
