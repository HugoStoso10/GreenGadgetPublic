#Bibliotecas
from passlib.context import CryptContext

#Este script serve para criar uma hash das passwords, garantindo segurança e privacidade ao utilizador

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def criar_hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verificar_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)