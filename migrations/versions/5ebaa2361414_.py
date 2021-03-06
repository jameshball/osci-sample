"""empty message

Revision ID: 5ebaa2361414
Revises: 1acb3d694b05
Create Date: 2021-06-30 16:58:12.363118

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5ebaa2361414'
down_revision = '1acb3d694b05'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('sample', sa.Column('anonymous', sa.Boolean(), nullable=True))
    op.create_foreign_key(None, 'sample', 'member', ['creator'], ['id'], ondelete='CASCADE', use_alter=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'sample', type_='foreignkey')
    op.drop_column('sample', 'anonymous')
    # ### end Alembic commands ###
