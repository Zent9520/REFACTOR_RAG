from sqlalchemy import (
    Integer,
    String,
    DateTime
)
from typing import Optional

from sqlalchemy.orm import (
    Mapped,
    mapped_column
)
from datetime import datetime

from uuid import uuid4

from app.core.database import Base

from sqlalchemy.dialects.postgresql import UUID

class Conversation(Base):
    
    __tablename__ = (
        
        "conversations"
        
    )
    id: Mapped[str] = (
        
        mapped_column(
            UUID(
                as_uuid=True
                ),
            primary_key = True,
            default=uuid4
        )
        
        
    )
    user_email: Mapped[Optional[str]] = mapped_column(
    String(50),
    nullable=True,
)
    title: Mapped[str|None] = (
        mapped_column(
            String(50),
            default="New chat"
        )
    )
    created_at: Mapped[datetime]= (
        mapped_column(
            DateTime,
            default=datetime.utcnow
        )
    )
    updated_at: Mapped[datetime]=(
        mapped_column(
            DateTime,
            default=datetime.utcnow
        )
    )
    
    
#     create table public.conversations (
#   id uuid not null default gen_random_uuid (),
#   user_email text not null,
#   title text not null default 'New Chat'::text,
#   created_at timestamp with time zone null default now(),
#   updated_at timestamp with time zone null default now(),
#   constraint conversations_pkey primary key (id)
# ) TABLESPACE pg_default;

# create index IF not exists idx_conversations_user on public.conversations using btree (user_email) TABLESPACE pg_default;
    