
from pydantic import BaseModel

class MessageAdd(BaseModel):
    sender_id : int
    receiver_id : int
    content : str
    is_read : bool
    
    class Config:
        from_attributes = True