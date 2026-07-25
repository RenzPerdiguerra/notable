from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    text,
)
from sqlalchemy.orm import relationship
from backend.app.db import Base


# This represents the authenticated person using the app.
# A user can own multiple notes and multiple AI chat sessions.
class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "management"}

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    # Role is used to distinguish regular users from admins or other future roles.
    role = Column(String(50), nullable=False, index=True, server_default="user")
    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    # A user can have many notes and many AI conversations.
    notes = relationship("Note", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")


# Composite index to speed up lookups by either email or username.
Index("ix_users_email_username", User.email, User.username)


# This is the main note entity. Each note belongs to one user and can be linked
# to a chat session if the user asks the AI about that specific content.
class Note(Base):
    __tablename__ = "notes"
    __table_args__ = {"schema": "management"}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("management.users.id", ondelete="CASCADE"), nullable=False)
    # Title is a short label for the note.
    title = Column(String(100), nullable=False)
    # Content is stored as JSON so the app can support rich note structures later.
    content = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"))
    updated_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship back to the owning user.
    user = relationship("User", back_populates="notes")
    # A note can be associated with one or more AI chat sessions.
    chat_sessions = relationship("ChatSession", back_populates="note", cascade="all, delete-orphan")


# This table stores which AI backend the app can use, such as Gemini or
# Hugging Face. The app can later switch between them per chat session.
class AI(Base):
    __tablename__ = "ai_providers"
    __table_args__ = {"schema": "management"}

    id = Column(Integer, primary_key=True, index=True)
    # Friendly display name for the provider, such as "Gemini" or "Hugging Face".
    name = Column(String(100), nullable=False, unique=True)
    # The provider family used by the app.
    provider_type = Column(String(50), nullable=False)  # gemini / huggingface
    # Optional model identifier, such as a Gemini model or HF model name.
    model_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    # Each AI provider can be used in many chat sessions.
    chat_sessions = relationship("ChatSession", back_populates="ai_provider", cascade="all, delete-orphan")


# A chat session is a temporary conversation container.
# It is useful for keeping a user's AI chat tied to a specific note and
# allowing it to expire after a set time.
class ChatSession(Base):
    __tablename__ = "chat_sessions"
    __table_args__ = {"schema": "management"}

    id = Column(Integer, primary_key=True, index=True)
    # Who owns this chat conversation.
    user_id = Column(Integer, ForeignKey("management.users.id", ondelete="CASCADE"), nullable=False)
    # Optional note context if the user is chatting about a particular note.
    note_id = Column(Integer, ForeignKey("management.notes.note_id", ondelete="SET NULL"), nullable=True)
    # Which AI backend is being used for this session.
    ai_id = Column(Integer, ForeignKey("management.ai_providers.ai_id", ondelete="SET NULL"), nullable=True)
    # A friendly title for the conversation, such as "Summarize today's notes".
    title = Column(String(150), nullable=True)
    # Optional expiration time for temporary sessions.
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"))
    updated_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships to the user, note, and AI provider.
    user = relationship("User", back_populates="chat_sessions")
    note = relationship("Note", back_populates="chat_sessions")
    ai_provider = relationship("AI", back_populates="chat_sessions")
    # A session contains multiple messages in order.
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


# Each message belongs to a session and stores the content of the user prompt
# or the AI response. This is what powers the chat-like experience.
class ChatMessage(Base):
    __tablename__ = "chat_messages"
    __table_args__ = {"schema": "management"}

    id = Column(Integer, primary_key=True, index=True)
    # Which conversation this message belongs to.
    session_id = Column(Integer, ForeignKey("management.chat_sessions.id", ondelete="CASCADE"), nullable=False)
    # Role helps distinguish user prompts from AI replies.
    role = Column(String(20), nullable=False)  # user / assistant / system
    # The actual text content of the message.
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    # Back-reference to the parent session.
    session = relationship("ChatSession", back_populates="messages")
    