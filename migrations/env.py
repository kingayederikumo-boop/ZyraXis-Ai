from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool
from app.config import Config
from app.database.models import Base

config = context.config
config.set_main_option("sqlalchemy.url", Config.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# ... (full env.py)