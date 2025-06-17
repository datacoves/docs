from typing import Optional

from django.core.exceptions import ValidationError
from pydantic import BaseModel, EmailStr
from pydantic import ValidationError as PydanticValidationError


class SMTPSettings(BaseModel):
    server: str
    host: str
    port: int
    mail_from: EmailStr
    user: Optional[str]
    password: Optional[str]
    ssl: Optional[bool] = False
    start_tls: Optional[bool] = True


def validate_smtp_settings(settings):
    if settings.get("server") == "custom":
        try:
            SMTPSettings(**settings)
        except PydanticValidationError as ex:
            raise ValidationError(ex)
