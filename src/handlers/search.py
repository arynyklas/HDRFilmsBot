from aiogram import Router, types
from rezka_api_sdk import RezkaAPI

import hashlib

from src import constants
from src.basic_data import TEXTS
from src.config import config


search_router = Router()


@search_router.inline_query()
async def search_inline_query(inline_query: types.InlineQuery, rezka_api: RezkaAPI) -> None:
    query = inline_query.query.strip()

    results: list[types.InlineQueryResult] = []

    if not query:
        await inline_query.answer(
            results = [],
            cache_time = config.inline_query_cache_time
        )

        return

    search_results = await rezka_api.search(query)

    for search_result in search_results:
        results.append(
            types.InlineQueryResultArticle(
                id = hashlib.md5(
                    string = search_result.id.encode(constants.ENCODING)
                ).hexdigest(),
                title = search_result.title,
                input_message_content = types.InputTextMessageContent(
                    message_text = TEXTS.inline_search.message_content.format(
                        image_url = search_result.image_url,
                        title = search_result.title,
                        url = search_result.url
                    )
                ),
                description = TEXTS.inline_search.result_description.format(
                    entity_text = constants.ENTITY_TYPE_TO_TEXT[search_result.entity_type.value],
                    addition = search_result.addition
                ),
                thumb_url = search_result.image_url
            )
        )

    await inline_query.answer(
        results = results,  # type: ignore
        cache_time = config.inline_query_cache_time
    )
