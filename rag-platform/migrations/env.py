"""Migration URL comes from environment, never from a checked-in configuration."""

import os

from alembic import context
from rag_api.identity.models import Base
from rag_api.identity.service import database_engine

engine = database_engine(os.environ["RAG_DATABASE_URL"])
with engine.connect() as connection:
    context.configure(connection=connection, target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()
engine.dispose()
