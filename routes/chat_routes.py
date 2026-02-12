from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from db import get_db
from models import Chat, Message, User
from schemas.chat_schemas import ChatOut, ChatCreate, MessageCreate
from utils.jwt_handler import verify_token
from utils.ai_response import get_completion
# We need OAuth2PasswordBearer to extract token from header
from fastapi.security import OAuth2PasswordBearer
import os

router = APIRouter(
    prefix="/chats",
    tags=["Chats"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # payload sub is strictly string, but ID is int
    try:
        user_id = int(payload.get("sub"))
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/", response_model=ChatOut)
def create_chat(chat_in: ChatCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Title defaults to "New Chat" if not provided
    title = chat_in.title or "New Chat"
    new_chat = Chat(user_id=current_user.id, title=title)
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)
    return new_chat

@router.get("/", response_model=List[ChatOut])
def get_chats(
    search: Optional[str] = None, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    query = db.query(Chat).filter(Chat.user_id == current_user.id)
    if search:
        query = query.filter(Chat.title.ilike(f"%{search}%"))
    
    # Order by newest first
    return query.order_by(Chat.created_at.desc()).all()

@router.get("/{chat_id}", response_model=ChatOut)
def get_chat(chat_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat

@router.post("/{chat_id}/message", response_model=ChatOut)
async def add_message(
    chat_id: int, 
    message_in: MessageCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # 1. Verify chat ownership
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    # 2. Save User Message
    user_msg = Message(chat_id=chat.id, role="user", content=message_in.content)
    db.add(user_msg)
    
    # Update chat title if it's new
    if len(chat.messages) == 0:
        # Simple heuristic: use first few words of message as title
        new_title = " ".join(message_in.content.split()[:5])
        chat.title = new_title

    db.commit() # Save user msg first

    # 3. Generate AI Response
    try:
        # Use shared utility with fallback logic
        ai_text = await get_completion(message_in.content)
        
    except Exception as e:
        ai_text = f"Error generating response: {str(e)}"

    # 4. Save AI Message
    ai_msg = Message(chat_id=chat.id, role="ai", content=ai_text)
    db.add(ai_msg)
    db.commit()
    db.refresh(chat) # Refresh to get updated messages list
    
    return chat
