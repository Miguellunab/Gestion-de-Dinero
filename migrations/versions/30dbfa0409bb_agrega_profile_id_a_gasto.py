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
    # Se crea la tabla profile
    op.create_table(
        'profile',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('pin', sa.String(length=4), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    # Actualizar la tabla gasto
    with op.batch_alter_table('gasto', schema=None) as batch_op:
        # Agregar la columna permitiendo NULL inicialmente
        batch_op.add_column(sa.Column('profile_id', sa.Integer(), nullable=True))
        # Actualizar registros existentes con un valor por defecto (ajusta el valor según corresponda)
        batch_op.execute('UPDATE gasto SET profile_id = 1')
        # Cambiar la columna para que ya no permita NULL
        batch_op.alter_column('profile_id', nullable=False)
        # Ajustar la columna monto
        batch_op.alter_column('monto',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               type_=sa.Integer(),
               existing_nullable=False)
        # Crear la llave foránea hacia profile
        batch_op.create_foreign_key(None, 'profile', ['profile_id'], ['id'])

    # Actualizar la tabla ingreso de forma similar
    with op.batch_alter_table('ingreso', schema=None) as batch_op:
        batch_op.add_column(sa.Column('profile_id', sa.Integer(), nullable=True))
        batch_op.execute('UPDATE ingreso SET profile_id = 1')
        batch_op.alter_column('profile_id', nullable=False)
        batch_op.alter_column('monto',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               type_=sa.Integer(),
               existing_nullable=False)
        batch_op.create_foreign_key(None, 'profile', ['profile_id'], ['id'])


def downgrade():
    # Revertir cambios en ingreso
    with op.batch_alter_table('ingreso', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.alter_column('monto',
               existing_type=sa.Integer(),
               type_=sa.DOUBLE_PRECISION(precision=53),
               existing_nullable=False)
        batch_op.drop_column('profile_id')
    # Revertir cambios en gasto
    with op.batch_alter_table('gasto', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.alter_column('monto',
               existing_type=sa.Integer(),
               type_=sa.DOUBLE_PRECISION(precision=53),
               existing_nullable=False)
        batch_op.drop_column('profile_id')
    op.drop_table('profile')
