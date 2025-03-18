from pathlib import Path

import re


VERSION_STR = "100624"

ENCODING = "utf-8"


WORK_DIRPATH = Path(__file__).parent.parent
LOGS_DIRPATH = WORK_DIRPATH / "logs"


if not LOGS_DIRPATH.exists():
    LOGS_DIRPATH.mkdir()


ENTITY_TYPE_TO_TEXT = {
    "films": "Фильм",
    "series": "Сериал",
    "animation": "Аниме",
    "cartoons": "Мультфильм"
}


TRANSLATOR_TEXT_PATTERN = re.compile(r"Озвучка:\s*<i>(.*?)</i>")
SERIES_DATA_PATTERN = re.compile(r"сезон\s*-\s*(\d+),\s*серия\s*-\s*(\d+)")
