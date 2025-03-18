import sqlalchemy as sa

from . import models
from .defs import DBSession


async def user_has_active_subscription(
    db_user: models.User,
    db_session: DBSession
) -> bool:
    query = sa.select(sa.exists().where(
        models.Subscription.user_id == db_user.id,
        models.Subscription.is_active == True  # noqa
    ))

    return (await db_session.execute(query)).scalar_one()


async def user_tracking_series(
    item_id: str,
    user_tg_id: int,
    db_session: DBSession
) -> bool:
    query = sa.select(sa.exists().where(
        models.TrackSeries.item_id == item_id,
        models.TrackSeries.user_tg_ids.contains([user_tg_id])
    ))

    return (await db_session.execute(query)).scalar_one()
