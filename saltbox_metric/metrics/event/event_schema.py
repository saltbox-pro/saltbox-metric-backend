from pydantic import BaseModel


class TaggedCountEventSchema(BaseModel):
    tag: str
    tag_name: str
    master_id: str
    payload_size: int


class PayloadSizeEventSchema(BaseModel):
    master_id: str
    payload_size: int
