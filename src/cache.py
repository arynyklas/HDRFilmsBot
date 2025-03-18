from rezka_api_sdk import RezkaAPI, models as rezka_models

import typing

from src import models, utils


K = typing.TypeVar("K")
V = typing.TypeVar("V")


class AsyncTimedCache(typing.Generic[K, V]):
    def __init__(self, expiration_time: int) -> None:
        self._cache: dict[K, tuple[V, float]] = {}
        self._expiration_time = expiration_time

    async def set(self, key: K, value: V) -> None:
        self._cache[key] = (value, utils.get_timestamp_float())

    async def get(self, key: K) -> V | None:
        if key in self._cache:
            value, timestamp = self._cache[key]

            if utils.get_timestamp_float() - timestamp < self._expiration_time:
                return value
            else:
                await self.remove(key)

        return None

    async def remove(self, key: K) -> None:
        if key in self._cache:
            del self._cache[key]

    async def clean_expired(self) -> None:
        current_time = utils.get_timestamp_float()

        keys_to_remove = [
            key
            for key, (_, timestamp) in self._cache.items()
            if current_time - timestamp >= self._expiration_time
        ]

        for key in keys_to_remove:
            await self.remove(key)


class BaseTimedRezkaCache(AsyncTimedCache[K, V]):
    def __init__(self, rezka_api: RezkaAPI, expiration_time: int) -> None:
        super().__init__(
            expiration_time = expiration_time
        )

        self._rezka_api = rezka_api

    async def get_or_set(self, *args: typing.Any, **kwargs: typing.Any) -> V:
        raise NotImplementedError


class AsyncTimedRezkaCacheData(BaseTimedRezkaCache[str, models.CachedRezkaData]):
    async def get_or_set(
        self,
        item_id: str,
        item_title: str,
        translator_id: str,
        translator_title: str,
        translator_additional_arguments: dict[str, str],
        is_film: bool,
        season_id: str | None = None,
        episode_id: str | None = None
    ):
        cache_rezka_data_key = models.CachedRezkaData.get_key(
            item_id = item_id,
            translator_id = translator_id,
            season_id = season_id,
            episode_id = episode_id
        )

        got_cached_rezka_data = await self.get(cache_rezka_data_key)

        if not got_cached_rezka_data:
            got_cached_rezka_data = models.CachedRezkaData.from_response(
                item_id = item_id,
                item_title = item_title,
                translator_id = translator_id,
                translator_title = translator_title,
                translator_additional_arguments = translator_additional_arguments,
                is_film = is_film,
                season_id = season_id,
                episode_id = episode_id,
                response = await self._rezka_api.get_direct_urls(
                    id = item_id,
                    is_film = is_film,
                    translator_id = translator_id,
                    translator_additional_arguments = translator_additional_arguments,
                    season_id = season_id,
                    episode_id = episode_id
                )
            )

            await self.set(
                key = cache_rezka_data_key,
                value = got_cached_rezka_data
            )

        return got_cached_rezka_data


class AsyncTimedRezkaCacheShortInfo(BaseTimedRezkaCache[str, tuple[rezka_models.ShortInfoModel, list[rezka_models.TranslatorInfoModel]]]):
    async def get_or_set(self, url: str):
        cache_key = url.split("/")[-1]

        got_cached_rezka_short_info = await self.get(cache_key)

        if not got_cached_rezka_short_info:
            got_cached_rezka_short_info = await self._rezka_api.get_info_and_translators(url)

            await self.set(
                key = cache_key,
                value = got_cached_rezka_short_info
            )

        return got_cached_rezka_short_info
