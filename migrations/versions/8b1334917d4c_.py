"""empty message

Revision ID: 8b1334917d4c
Revises: ab8e325c8c6e
Create Date: 2017-08-23 16:32:45.953275

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8b1334917d4c'
down_revision = 'ab8e325c8c6e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('bots', sa.Column('active_model', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('bots', 'active_model')
    # ### end Alembic commands ###
