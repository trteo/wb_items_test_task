from pydantic import BaseModel


class ProductPosition(BaseModel):
    page_number: int
    position_on_page: int
