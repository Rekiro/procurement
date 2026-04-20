import asyncio
import sys
from logging.config import fileConfig

# Windows: psycopg async requires SelectorEventLoop
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

from app.config import settings
from app.database import Base

# Import all proc_* models so Alembic detects them.
# Note: the shared `api_logs` table (ApiLog) is owned by accountMaster's
# alembic chain. It's imported here only so SQLAlchemy ORM can use it; the
# `include_object` filter below excludes it from procurement's autogenerate.
from app.logging.models import ApiLog  # noqa: F401
from app.procurement.vendors.models import ProcVendor, ProcVendorApplication  # noqa: F401
from app.procurement.products.models import ProcProduct, ProcProductPriceChangeRequest  # noqa: F401
from app.procurement.extra_material_requests.models import ProcExtraMaterialRequest  # noqa: F401
from app.procurement.indents.models import ProcIndent, ProcIndentItem  # noqa: F401
from app.procurement.purchase_orders.models import ProcPurchaseOrder, ProcPoItem, ProcGrn, ProcGrnItem, ProcGrnPhoto  # noqa: F401
from app.procurement.invoices.models import ProcInvoice, ProcInvoicePoLink  # noqa: F401
from app.procurement.cash_purchases.models import ProcCashPurchase  # noqa: F401
from app.procurement.machinery_requests.models import ProcMachineryRequest, ProcMachineryPurchaseOrder, ProcMachineryGrn  # noqa: F401
from app.procurement.uniform_requests.models import ProcUniformRequest, ProcUniformPurchaseOrder  # noqa: F401
from app.procurement.notifications.models import ProcNotification  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Procurement shares the smarterp DB with account-master, accounts, payroll,
# and survey. Each of those lives in its own schema. Procurement's own tables
# (proc_*) still live in public for now. Autogenerate must only consider
# tables in schemas this app owns, otherwise it would propose dropping
# sibling apps' tables.
OWNED_SCHEMAS = {"public"}
# Tables in `public` that are NOT owned by procurement (none today — the
# shared tables moved to the `shared` schema).
EXTERNAL_TABLES_IN_PUBLIC: set[str] = set()

# Procurement's migration history is tracked in its own alembic version table
# so it doesn't collide with commercial-backend's default `alembic_version`
# in the same database.
VERSION_TABLE = "alembic_version_procurement"


def include_object(object_, name, type_, reflected, compare_to):
    if type_ == "table":
        schema = getattr(object_, "schema", None) or "public"
        if schema not in OWNED_SCHEMAS:
            return False
        if name in EXTERNAL_TABLES_IN_PUBLIC:
            return False
    return True


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        version_table=VERSION_TABLE,
        include_object=include_object,
        include_schemas=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        version_table=VERSION_TABLE,
        include_object=include_object,
        include_schemas=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
