import uuid
from sqlalchemy.types import TypeDecorator
from sqlalchemy.dialects.mysql import BINARY

class UUIDBinary(TypeDecorator):
    """UUID stored as BINARY(16) with automatical convertion"""
    impl = BINARY(16)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value.bytes
        if isinstance(value, bytes):
            return value
        return uuid.UUID(value).bytes

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return uuid.UUID(bytes=value)
