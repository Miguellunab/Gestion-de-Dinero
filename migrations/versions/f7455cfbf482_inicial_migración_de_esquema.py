"""Inicial migración de esquema

Revision ID: f7455cfbf482
Revises: 
Create Date: 2025-03-23 15:07:53.255856

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f7455cfbf482'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('gasto',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('monto', sa.Float(), nullable=False),
    sa.Column('descripcion', sa.String(length=200), nullable=True),
    sa.Column('fecha', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('ingreso',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('monto', sa.Float(), nullable=False),
    sa.Column('descripcion', sa.String(length=200), nullable=True),
    sa.Column('fecha', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('ingreso')
    op.drop_table('gasto')
    # ### end Alembic commands ###
