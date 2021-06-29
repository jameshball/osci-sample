from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

db = SQLAlchemy(engine_options={"max_overflow": -1})

# ANY UPDATES TO MODEL NEED TO BE APPLIED TO TEST/PROD DATABASES USING FLASK-MIGRATE/ALEMBIC
# https://flask-migrate.readthedocs.io/en/latest/


class Sample(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, server_default=func.now())

    creator = db.Column(db.Integer, db.ForeignKey('member.id', ondelete='CASCADE', use_alter=True), nullable=False)

    name = db.Column(db.String(), nullable=False)
    description = db.Column(db.Text, nullable=False)
    audio_data = db.Column(db.LargeBinary, nullable=False)
    sample_rate = db.Column(db.Integer, nullable=True)
    bit_depth = db.Column(db.Integer, nullable=True)
    num_downloads = db.Column(db.Integer, nullable=False, default=0)


class Member(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    google_id = db.Column(db.Text, unique=True, nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())

    first_name = db.Column(db.String(), nullable=False)
    last_name = db.Column(db.String(), nullable=False)
    username = db.Column(db.String(), nullable=True)
    email = db.Column(db.Text, unique=True, nullable=False)
    profile_pic = db.Column(db.Text, nullable=True)

    def get_id(self):
        return str(self.google_id)
