from .start import start_router
from .search import search_router
from .payments import payments_router
from .short_info import short_info_router
from .callback_query import callback_query_router


ROUTERS = (
    start_router,
    search_router,
    payments_router,
    short_info_router,
    callback_query_router
)
