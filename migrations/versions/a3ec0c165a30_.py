"""empty message

Revision ID: a3ec0c165a30
Revises: daa12e91b319
Create Date: 2019-05-16 18:26:13.640607

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a3ec0c165a30'
down_revision = 'daa12e91b319'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('message', 'text',
               existing_type=sa.VARCHAR(),
               nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('message', 'text',
               existing_type=sa.VARCHAR(),
               nullable=True)
    # ### end Alembic commands ###