from argon2.low_level import hash_secret_raw, Type
import base64
import getpass


def argon2id(secret: bytes, salt: bytes) -> str:
    raw = hash_secret_raw(
        secret=secret,
        salt=salt,
        time_cost=3,
        memory_cost=65536,
        parallelism=4,
        hash_len=32,
        type=Type.ID,
    )
    password = base64.urlsafe_b64encode(raw).decode()
    return password


secret = getpass.getpass("Secret: ").encode("utf-8")
salt = getpass.getpass("Salt: ").encode("utf-8")
print(argon2id(secret, salt))
