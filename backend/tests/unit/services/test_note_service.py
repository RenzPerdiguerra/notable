import pytest
from backend.app.services.note_service import create_note, get_note, list_notes, update_note, delete_note
from backend.app.schemas.note import NoteCreate, NoteUpdate

def test_create_note(db_session, user):
    note_in = NoteCreate(title="My Note", content={"text": "Hello"})
    note = create_note(db_session, note_in, user_id=user.id)
    assert note.id is not None
    assert note.title == "My Note"

def test_get_note(db_session, user):
    note_in = NoteCreate(title="My Note", content={"text": "Hello"})
    note = create_note(db_session, note_in, user_id=user.id)
    fetched = get_note(db_session, note.id, user_id=user.id)
    assert fetched.id == note.id

    hidden = get_note(db_session, note.id, user_id=user.id + 1)
    assert hidden is None

def test_list_notes(db_session, user):
    note_in = NoteCreate(title="Note A", content={"text": "A"})
    create_note(db_session, note_in, user_id=user.id)
    notes = list_notes(db_session, user_id=user.id)
    assert len(notes) >= 1

def test_update_note(db_session, user):
    note_in = NoteCreate(title="Old Title", content={"text": "Hello"})
    note = create_note(db_session, note_in, user_id=user.id)
    update_in = NoteUpdate(title="New Title")
    updated = update_note(db_session, note.id, update_in, user_id=user.id)
    assert updated.title == "New Title"
    assert updated.updated_at is not None

    hidden = update_note(db_session, note.id, NoteUpdate(title="Hijacked"), user_id=user.id + 1)
    assert hidden is None

def test_delete_note(db_session, user):
    note_in = NoteCreate(title="Delete Me", content={"text": "Bye"})
    note = create_note(db_session, note_in, user_id=user.id)
    assert not delete_note(db_session, note.id, user_id=user.id + 1)
    success = delete_note(db_session, note.id, user_id=user.id)
    assert success
    assert get_note(db_session, note.id, user_id=user.id) is None
