from pydantic import BaseModel


class ElectricForm(BaseModel):
    username: str
    password: str
    query: str
    factoryCode: str


class BooksForm(BaseModel):
    username: str
    password: str
