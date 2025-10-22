# models/users
from tortoise import fields
from tortoise.models import Model
from enum import IntEnum

from backend.models.users_roles import UserRole

# Статусы пользователя в системе (наследуем от IntEnum для хранения в БД как чисел)
class UserStatus(IntEnum):
    BANNED = 0    # Заблокированный аккаунт
    ACTIVE = 1     # Активный пользователь
    PENDING = 2    # Ожидает активации

class User(Model):
    id = fields.IntField(pk=True)
    login = fields.CharField(50, unique=True)
    hashed_password = fields.CharField(128)
    role = fields.CharEnumField(UserRole, default=UserRole.user)
    status = fields.IntEnumField(UserStatus, default=UserStatus.ACTIVE)

    class Meta:
        table = "users"