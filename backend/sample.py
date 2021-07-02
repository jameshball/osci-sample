import os
import time
from datetime import datetime
from tempfile import NamedTemporaryFile

from flask import Blueprint, request, Response, abort, send_file, redirect, url_for
from flask_login import current_user, login_required

from backend.model import db, Member, Sample

sample = Blueprint('sample', __name__)

download_map = {}


@sample.route('/sample/<int:sample_id>')
def download_sample(sample_id):
    sample = Sample.query.get_or_404(sample_id)
    file_ext = sample.name.rsplit('.', 1)[1].lower()
    temp = NamedTemporaryFile(suffix="." + file_ext, delete=False)
    temp.write(sample.audio_data)
    temp.close()

    if sample_id not in download_map:
        download_map[sample_id] = []

    if (header := request.headers.get("X-Forwarded-For")) is not None:
        ip = header.split(',')[0]
    else:
        ip = request.remote_addr

    if ip not in download_map[sample_id]:
        sample.num_downloads = Sample.num_downloads + 1
        download_map[sample_id].append(ip)
        db.session.commit()

    return send_file(temp.name)


@sample.route('/sample/<int:sample_id>/delete', methods=['DELETE'])
@login_required
def delete_sample(sample_id):
    sample = Sample.query.get(sample_id)
    if current_user.id != sample.creator:
        abort(401)

    Sample.query.filter(Sample.id == sample_id).delete()
    db.session.commit()

    return ''


def get_samples():
    samples = Sample.query.all()

    samples.sort(key=lambda s: s.num_downloads, reverse=True)

    samples_obj = []
    for sample in samples:
        creator = Member.query.get(sample.creator)

        samples_obj.append({
            'id': sample.id,
            'name': sample.name,
            'description': sample.description,
            'creator': sample.creator,
            'sample_rate': sample.sample_rate,
            'bit_depth': sample.bit_depth,
            'num_downloads': sample.num_downloads,
            'anonymous': sample.anonymous,
            'first_name': None if sample.anonymous else creator.first_name,
            'last_name': None if sample.anonymous else creator.last_name,
            'username': None if sample.anonymous else creator.username,
        })

    return samples_obj
