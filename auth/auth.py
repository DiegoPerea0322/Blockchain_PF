# auth/auth.py
from pydantic import BaseModel

class User(BaseModel):
    username: str
    password: str
    role: str  # "usuario" or "autoridad"

# Users: includes validator accounts (their username matches validator node ids)
USERS_DB = {
    "alice": User(username="alice", password="alicepw", role="usuario"),
    "maria": User(username="maria", password="mariapw", role="usuario"),
    "validator_1": User(username="validator_1", password="valpw", role="autoridad"),
    "validator_2": User(username="validator_2", password="valpw", role="autoridad"),
    "validator_3": User(username="validator_3", password="valpw", role="autoridad"),
    "validator_4": User(username="validator_4", password="valpw", role="autoridad"),
    "validator_5": User(username="validator_5", password="valpw", role="autoridad")
}

def authenticate(username: str, password: str):
    user = USERS_DB.get(username)
    if not user or user.password != password:
        return None
    return user

def get_user_by_username(username: str):
    return USERS_DB.get(username)
