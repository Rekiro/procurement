import math

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession


async def paginate(query, db: AsyncSession, page: int = 1, limit: int = 10):
    """Execute a query with pagination and return (items, pagination_meta).

    Returns:
        (list[Row], dict) where dict has currentPage, totalPages, totalItems
    """
    if page < 1:
        page = 1
    if limit < 1:
        limit = 10

    # Count total rows
    count_q = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_q) or 0

    # Apply offset/limit
    offset = (page - 1) * limit
    paginated_q = query.offset(offset).limit(limit)
    result = await db.execute(paginated_q)
    items = list(result.scalars().all())

    pagination = {
        "currentPage": page,
        "totalPages": math.ceil(total / limit) if limit else 1,
        "totalItems": total,
    }
    return items, pagination
