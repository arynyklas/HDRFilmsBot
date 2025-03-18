from cryptography.hazmat.primitives import serialization
from jwt import PyJWT

import typing

from src import constants
from src.config import config


ALGORITHM = "ES256"

if config.private_key_filename:
    PRIVATE_KEY_OBJ = serialization.load_pem_private_key(
        (constants.WORK_DIRPATH / config.private_key_filename).read_bytes(),
        None
    )


jwt = PyJWT()


def sort_obj_keys_alphabetically(data: dict[str, typing.Any] | typing.Any) -> dict[str, typing.Any] | typing.Any:
    # TODO: fix typehints; remove `type: ignore`
    if isinstance(data, dict):
        return {
            key: sort_obj_keys_alphabetically(data[key])  # type: ignore
            for key in sorted(data)  # type: ignore
        }

    return data


if config.private_key_filename:
    def encrypt(data: dict[str, typing.Any]) -> str:
        return jwt.encode(
            payload = sort_obj_keys_alphabetically(data),
            key = PRIVATE_KEY_OBJ,  # type: ignore
            algorithm = ALGORITHM
        )
