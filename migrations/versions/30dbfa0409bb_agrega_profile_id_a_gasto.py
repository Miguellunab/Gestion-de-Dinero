"""Agrega profile_id a gasto

Revision ID: 30dbfa0409bb
Revises: f7455cfbf482
Create Date: 2025-03-23 22:33:58.524117

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '30dbfa0409bb'
down_revision = 'f7455cfbf482'
branch_labels = None
depends_on = None


def upgrade():
    # Crear la tabla profile
    op.create_table(
        'profile',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('pin', sa.String(length=4), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Para la tabla gasto:
    # 1. Agregar la columna profile_id como nullable y ajustar la columna monto
    with op.batch_alter_table('gasto', schema=None) as batch_op:
        batch_op.add_column(sa.Column('profile_id', sa.Integer(), nullable=True))
        batch_op.alter_column(
            'monto',
            existing_type=sa.DOUBLE_PRECISION(precision=53),
            type_=sa.Integer(),
            existing_nullable=False
        )
    # 2. Actualizar los registros existentes para asignar un valor (asegúrate de que exista un profile con id=1)
    op.execute('UPDATE gasto SET profile_id = 1')
    # 3. Alterar la columna profile_id para que sea NOT NULL y crear la llave foránea
    with op.batch_alter_table('gasto', schema=None) as batch_op:
        batch_op.alter_column('profile_id', nullable=False)
        batch_op.create_foreign_key(None, 'profile', ['profile_id'], ['id'])
    
    # Para la tabla ingreso (proceso similar):
    with op.batch_alter_table('ingreso', schema=None) as batch_op:
        batch_op.add_column(sa.Column('profile_id', sa.Integer(), nullable=True))
        batch_op.alter_column(
            'monto',
            existing_type=sa.DOUBLE_PRECISION(precision=53),
            type_=sa.Integer(),
            existing_nullable=False
        )
    op.execute('UPDATE ingreso SET profile_id = 1')
    with op.batch_alter_table('ingreso', schema=None) as batch_op:
        batch_op.alter_column('profile_id', nullable=False)
        batch_op.create_foreign_key(None, 'profile', ['profile_id'], ['id'])


def downgrade():
    # Revertir cambios en la tabla ingreso
    with op.batch_alter_table('ingreso', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.alter_column(
            'monto',
            existing_type=sa.Integer(),
            type_=sa.DOUBLE_PRECISION(precision=53),
            existing_nullable=False
        )
        batch_op.drop_column('profile_id')
    # Revertir cambios en la tabla gasto
    with op.batch_alter_table('gasto', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.alter_column(
            'monto',
            existing_type=sa.Integer(),
            type_=sa.DOUBLE_PRECISION(precision=53),
            existing_nullable=False
        )
        batch_op.drop_column('profile_id')
    op.drop_table('profile')
