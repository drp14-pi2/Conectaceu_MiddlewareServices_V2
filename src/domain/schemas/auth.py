"""Auth schemas"""
from pydantic import BaseModel

class Login(BaseModel):
    document: str
    password: str
