"""Agrega cuentas a los ingresos y los gastos

Revision ID: 380f1ba9664e
Revises: 30dbfa0409bb
Create Date: 2025-04-03 11:15:48.834761

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '380f1ba9664e'
down_revision = '30dbfa0409bb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('gasto', schema=None) as batch_op:
        batch_op.add_column(sa.Column('cuenta', sa.String(length=50), nullable=True))

    with op.batch_alter_table('ingreso', schema=None) as batch_op:
        batch_op.add_column(sa.Column('cuenta', sa.String(length=50), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('ingreso', schema=None) as batch_op:
        batch_op.drop_column('cuenta')

    with op.batch_alter_table('gasto', schema=None) as batch_op:
        batch_op.drop_column('cuenta')

    # ### end Alembic commands ###
