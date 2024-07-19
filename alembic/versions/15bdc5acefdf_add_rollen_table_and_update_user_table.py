"""Add Rollen table and update User table

Revision ID: 15bdc5acefdf
Revises: 4c07830d0318
Create Date: 2024-07-17 22:37:18.598587

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.sql import table, column


# revision identifiers, used by Alembic.
revision: str = '15bdc5acefdf'
down_revision: Union[str, None] = '4c07830d0318'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def table_exists(table_name):
    inspector = Inspector.from_engine(op.get_bind())
    return table_name in inspector.get_table_names()

def upgrade():
    # Create Rollen table if it doesn't exist
    if not table_exists('rollen'):
        op.create_table('rollen',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('naam', sa.String(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_rollen_naam'), 'rollen', ['naam'], unique=True)

        # Insert default roles
        op.execute("INSERT INTO rollen (naam) VALUES ('Administrator'), ('Beheerder'), ('Gebruiker')")
    
    # Check if rol_id column already exists in user table
    inspector = Inspector.from_engine(op.get_bind())
    user_columns = [col['name'] for col in inspector.get_columns('user')]

    if 'rol_id' not in user_columns:
        # Add rol_id column to user table
        op.add_column('user', sa.Column('rol_id', sa.Integer(), nullable=True))
    
    # Update existing users to have a default role (e.g., 'Gebruiker')
    connection = op.get_bind()
    user_table = table('user',
        column('id', sa.Integer),
        column('rol_id', sa.Integer),
        column('role', sa.String)
    )
    rollen_table = table('rollen',
        column('id', sa.Integer),
        column('naam', sa.String)
    )

    # First, make sure all users have a rol_id
    connection.execute(
        user_table.update().where(user_table.c.rol_id == None).values(
            rol_id=connection.execute(
                sa.select([rollen_table.c.id]).where(rollen_table.c.naam == 'Gebruiker')
            ).scalar()
        )
    )

    # Then, if the old 'role' column exists, update rol_id based on it
    if 'role' in user_columns:
        for old_role in ['Administrator', 'Beheerder', 'Gebruiker']:
            connection.execute(
                user_table.update().where(user_table.c.role == old_role).values(
                    rol_id=connection.execute(
                        sa.select([rollen_table.c.id]).where(rollen_table.c.naam == old_role)
                    ).scalar()
                )
            )

    # Now we can safely make rol_id not nullable
    with op.batch_alter_table('user') as batch_op:
        batch_op.alter_column('rol_id', nullable=False)
    
    # Add foreign key constraint
    with op.batch_alter_table('user') as batch_op:
        batch_op.create_foreign_key(None, 'rollen', ['rol_id'], ['id'])
    
    # Remove old role column if it exists
    if 'role' in user_columns:
        with op.batch_alter_table('user') as batch_op:
            batch_op.drop_column('role')

def downgrade():
    # Add back the old role column
    with op.batch_alter_table('user') as batch_op:
        batch_op.add_column(sa.Column('role', sa.String(), nullable=True))
    
    # Copy data from rollen to role
    op.execute("""
    UPDATE user
    SET role = (SELECT naam FROM rollen WHERE rollen.id = user.rol_id)
    """)
    
    # Remove the foreign key constraint and rol_id column
    with op.batch_alter_table('user') as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('rol_id')
    
    # Drop the Rollen table
    op.drop_index(op.f('ix_rollen_naam'), table_name='rollen')
    op.drop_table('rollen')
    # ### end Alembic commands ###
