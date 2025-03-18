from pydantic import BaseModel, Field
from typing_extensions import Self

from rezka_api_sdk.models import DirectURLsModel


class CachedRezkaData(BaseModel):
    item_id: str
    item_title: str
    translator_id: str
    translator_title: str
    translator_additional_arguments: dict[str, str] = Field(default_factory=dict)
    is_film: bool
    season_id: str | None
    episode_id: str | None
    seasons: dict[str, str] | None
    episodes: dict[str, dict[str, str]] | None
    urls: dict[str, str] | None
    subtitles: dict[str, str] | None
    subtitle_languages: dict[str, str] | None

    @staticmethod
    def get_key(
        item_id: str,
        translator_id: str,
        season_id: str | None = None,
        episode_id: str | None = None
    ) -> str:
        key = f"{item_id}_{translator_id}"

        if season_id is not None:
            key += f"_{season_id}"

        if episode_id is not None:
            key += f"_{episode_id}"

        return key

    @classmethod
    def from_response(
        cls,
        item_id: str,
        item_title: str,
        translator_id: str,
        translator_title: str,
        translator_additional_arguments: dict[str, str],
        is_film: bool,
        response: DirectURLsModel,
        season_id: str | None = None,
        episode_id: str | None = None
    ) -> Self:
        return cls(
            item_id = item_id,
            item_title = item_title,
            translator_id = translator_id,
            translator_title = translator_title,
            translator_additional_arguments = translator_additional_arguments,
            is_film = is_film,
            season_id = season_id,
            episode_id = episode_id,
            seasons = response.seasons,
            episodes = response.episodes,
            urls = response.urls,
            subtitles = response.subtitles,
            subtitle_languages = response.subtitle_languages
        )
