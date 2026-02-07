from pydantic import BaseModel

class User_schemas(BaseModel):
    email:str
    password:str
