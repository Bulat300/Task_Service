from sqlalchemy import MetaData, Integer, Column
from sqlalchemy.orm import DeclarativeBase, declared_attr

metadata = MetaData()

class Base(DeclarativeBase):
    metadata = metadata

    @declared_attr
    def id(cls):
        return Column(Integer, primary_key=True, index=True)