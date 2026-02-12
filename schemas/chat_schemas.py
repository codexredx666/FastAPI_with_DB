from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class MessageBase(BaseModel):
    role: str
    content: str

class MessageCreate(MessageBase):
    pass

class MessageOut(MessageBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
        orm_mode = True

class ChatBase(BaseModel):
    title: Optional[str] = None

class ChatCreate(ChatBase):
    pass

class ChatOut(ChatBase):
    id: int
    title: str
    created_at: datetime
    messages: List[MessageOut] = []
    
    class Config:
        from_attributes = True
        orm_mode = True
