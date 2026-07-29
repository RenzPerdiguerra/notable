from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from backend.app.models.model import Note
from backend.app.schemas.note import NoteCreate, NoteUpdate


def create_note(db: Session, note_in: NoteCreate) -> Note:
    if note_in.user_id is None:
        raise ValueError("user_id is required")

    note = Note(
        user_id=note_in.user_id,
        title=note_in.title.strip(),
        content=note_in.content,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def get_note(db: Session, note_id: int) -> Optional[Note]:
    return db.query(Note).filter(Note.id == note_id).first()


def list_notes(db: Session, user_id: Optional[int] = None) -> list[Note]:
    query = db.query(Note)
    if user_id is not None:
        query = query.filter(Note.user_id == user_id)
    return query.order_by(Note.created_at.desc()).all()


def update_note(db: Session, note_id: int, note_in: NoteUpdate) -> Optional[Note]:
    note = get_note(db, note_id)
    if not note:
        return None

    if note_in.title is not None:
        note.title = note_in.title.strip()

    if note_in.content is not None:
        note.content = note_in.content

    note.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(note)
    return note


def delete_note(db: Session, note_id: int) -> bool:
    note = get_note(db, note_id)
    if not note:
        return False

    db.delete(note)
    db.commit()
    return True
