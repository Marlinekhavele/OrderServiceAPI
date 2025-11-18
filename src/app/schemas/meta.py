from pydantic import BaseModel


class Meta(BaseModel):
    app_version: str


__all__ = ["Meta"]
