from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import padding as crypt_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from jwt import PyJWT
from base64 import b64encode

import os
import simplejson as json
import hashlib
import typing

from src import constants
from src.config import config


ALGORITHM = "ES256"


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
    PRIVATE_KEY_OBJ = serialization.load_pem_private_key(
        (constants.WORK_DIRPATH / config.private_key_filename).read_bytes(),
        None
    )

    def encrypt_external_player_params(data: dict[str, typing.Any]) -> str:
        return jwt.encode(
            payload = sort_obj_keys_alphabetically(data),
            key = PRIVATE_KEY_OBJ,  # type: ignore
            algorithm = ALGORITHM
        )


proxied_urls_key = hashlib.sha256(config.proxied_urls_secret.encode()).digest()


def get_proxied_view_urls_params(data: dict[str, typing.Any]) -> str:
    padder = crypt_padding.PKCS7(128).padder()
    padded = padder.update(json.dumps(data).encode('utf-8')) + padder.finalize()
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(proxied_urls_key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()

    return b64encode(iv + ciphertext).decode('utf-8')
