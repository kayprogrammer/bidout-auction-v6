from pydantic import BaseModel, validator, Field, EmailStr
from .base import ResponseSchema


class RegisterUserSchema(BaseModel):
    first_name: str = Field(..., example="John", max_length=50)
    last_name: str = Field(..., example="Doe", max_length=50)
    email: EmailStr = Field(..., example="johndoe@example.com")
    password: str = Field(..., example="strongpassword", min_length=8)
    terms_agreement: bool

    @validator("first_name", "last_name")
    def validate_name(cls, v):
        if len(v.split(" ")) > 1:
            raise ValueError("No spacing allowed")
        return v

    @validator("terms_agreement")
    def validate_terms_agreement(cls, v):
        if not v:
            raise ValueError("You must agree to terms and conditions")
        return v

    class Config:
        error_msg_templates = {
            "value_error.any_str.max_length": "50 characters max!",
            "value_error.any_str.min_length": "8 characters min!",
        }


class VerifyOtpSchema(BaseModel):
    email: EmailStr = Field(..., example="johndoe@example.com")
    otp: int


class RequestOtpSchema(BaseModel):
    email: EmailStr = Field(..., example="johndoe@example.com")


class SetNewPasswordSchema(BaseModel):
    email: EmailStr = Field(..., example="johndoe@example.com")
    otp: int
    password: str = Field(..., example="newstrongpassword", min_length=8)

    class Config:
        error_msg_templates = {
            "value_error.any_str.min_length": "8 characters min!",
        }


class LoginUserSchema(BaseModel):
    email: EmailStr = Field(..., example="johndoe@example.com")
    password: str = Field(..., example="password")


class RefreshTokensSchema(BaseModel):
    refresh: str = Field(
        ...,
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
    )


class RegisterResponseSchema(ResponseSchema):
    data: RequestOtpSchema


class TokensResponseDataSchema(BaseModel):
    access: str = Field(
        ...,
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
    )
    refresh: str = Field(
        ...,
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
    )


class TokensResponseSchema(ResponseSchema):
    data: TokensResponseDataSchema
