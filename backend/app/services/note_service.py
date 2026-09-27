from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from backend.app.models.model import Note
from backend.app.schemas.note import NoteCreate, NoteUpdate


def create_note(db: Session, note_in: NoteCreate, user_id: int) -> Note:
    note = Note(
        user_id=user_id,
        title=note_in.title.strip(),
        content=note_in.content,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def get_note(db: Session, note_id: int, user_id: int) -> Optional[Note]:
    return db.query(Note).filter(Note.id == note_id, Note.user_id == user_id).first()


def list_notes(db: Session, user_id: int) -> list[Note]:
    return (
        db.query(Note)
        .filter(Note.user_id == user_id)
        .order_by(Note.created_at.desc())
        .all()
    )


def update_note(db: Session, note_id: int, note_in: NoteUpdate, user_id: int) -> Optional[Note]:
    note = get_note(db, note_id, user_id)
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


def delete_note(db: Session, note_id: int, user_id: int) -> bool:
    note = get_note(db, note_id, user_id)
    if not note:
        return False

    db.delete(note)
    db.commit()
    return True
