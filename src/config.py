from pydantic import BaseModel, Field
from pathlib import Path

import sys
import yaml

from src import constants


CONFIG_FILEPATH = constants.WORK_DIRPATH / (
    "config.test.yml"
    if "--test" in sys.argv
    else
    "config.yml"
)


class SubscriptionConfig(BaseModel):
    price: int
    days: int
    currency: str


class Config(BaseModel):
    bot_token: str
    logger_name: str
    logs_chat_id: int
    logger_chat_level: str
    logger_file_level: str
    admins: list[int]
    db_url: str
    users_messages_per_second: int
    rezka_api_url: str | None = Field(default=None)
    rezka_api_key: str
    private_key_filename: str | None = Field(default=None)
    external_player_url: str | None = Field(default=None)
    proxied_view_url: str
    proxied_urls_secret: str
    log_filename: str
    custom_bot_api_server: str
    subscription: SubscriptionConfig
    downloads_temp_dirpath: Path
    max_file_upload_size: int
    track_series_checker_delay: float
    track_series_checker_per_message_delay: float
    track_series_checker_per_delay: float
    download_items_queue_per_message_delay: float
    download_items_queue_to_chat_id: int
    inline_query_cache_time: int
    cache_rezka_data_time: int
    cache_rezka_short_info_time: int


with CONFIG_FILEPATH.open("r", encoding="utf-8") as file:
    config = Config.model_validate(yaml.safe_load(file))
