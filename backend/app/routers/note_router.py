from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.db import get_db
from backend.app.schemas.note import NoteCreate, NoteOut, NoteUpdate
from backend.app.services.note_service import create_note, delete_note, get_note, list_notes, update_note

router = APIRouter(prefix="/notes", tags=["Notes"])


@router.post("/", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
def api_create_note(note_in: NoteCreate, db: Session = Depends(get_db)):
    return create_note(db=db, note_in=note_in)


@router.get("/{note_id}", response_model=NoteOut)
def api_get_note(note_id: int, db: Session = Depends(get_db)):
    note = get_note(db=db, note_id=note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.get("/", response_model=list[NoteOut])
def api_list_notes(user_id: Optional[int] = None, db: Session = Depends(get_db)):
    return list_notes(db=db, user_id=user_id)


@router.put("/{note_id}", response_model=NoteOut)
def api_update_note(note_id: int, note_in: NoteUpdate, db: Session = Depends(get_db)):
    note = update_note(db=db, note_id=note_id, note_in=note_in)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def api_delete_note(note_id: int, db: Session = Depends(get_db)):
    success = delete_note(db=db, note_id=note_id)
    if not success:
        raise HTTPException(status_code=404, detail="Note not found")
    return None