from pydantic import BaseModel

class AddItRequest(BaseModel):
    product_url: str | None = None

class AddItResponse(BaseModel):
    agent_finished: bool

class FindItRequest(BaseModel):
    image_data: str | None = None
    image_url: str | None = None
    user_prompt: str | None = None

class FindItResponse(BaseModel):
    amazon_link: list[str] | str | None = None
    item_description: str | None = None
    is_found: bool

class SearchSimilarRequest(BaseModel):
    product_description: str | None = None

class SearchSimilarResponse(BaseModel):
    amazon_links: list[str] | str | None = None