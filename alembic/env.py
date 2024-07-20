from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Dit is de Alembic Config object, die voorziet
# in toegang tot de waarden binnen de .ini file in gebruik.
config = context.config

# Interpreteer de config file voor Python logging.
# Deze lijn stelt logging in voor de hele toepassing.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Voeg hier je model's MetaData object toe
# voor 'autogenerate' ondersteuning
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
from app.models import models  # Pas dit pad aan naar waar je modellen zijn gedefinieerd
from app.database import engine  # Importeer je engine

target_metadata = models.SQLModel.metadata

# Andere waarden van config, gedefinieerd door de behoeften van env.py,
# kunnen worden verkregen:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()