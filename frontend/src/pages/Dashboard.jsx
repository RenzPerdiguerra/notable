import { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { aiApi, notesApi } from '../api/api';


export default function Dashboard() {
    const [noteTitle, setNoteTitle] = useState("")
    const [noteContent, setNoteContent] = useState("")
    const [selectedNote, setSelectedNote] = useState(null)
    const [activeDraft, setActiveDraft] = useState(null)
    const [draftNotes, setDraftNotes] = useState([])
    const [pendingChanges, setPendingChanges] = useState({})
    const [openSettingsId, setOpenSettingsId] = useState(null)
    const [renamingItemId, setRenamingItemId] = useState(null)
    const [renameValue, setRenameValue] = useState("")
    const [isEditingTitle, setIsEditingTitle] = useState(false)
    const [aiQuestion, setAiQuestion] = useState("")
    const [aiResponse, setAiResponse] = useState("")
    const [aiLoading, setAiLoading] = useState("")
    const [aiProvider, setaiProvider] = useState("")
    const navigate = useNavigate()
    const queryClient = useQueryClient()
    const nextDraftId = useRef(1)

    // TODO: Fill with process for logout to remove user session (secure)
    // TODO: handleDropDown for adding user profile, settings, log/monitoring
    const handleLogout = () => {
        navigate("/login")
    }

    const { data: notes, isLoading} = useQuery({
        queryKey: ["notes"],
        queryFn: () => notesApi.getAll().then(r => r.data)
    })

    const saveMutation = useMutation({
        mutationFn: ({ kind, id, data }) => kind === "create"
            ? notesApi.create(data)
            : notesApi.update(id, data),
        onSuccess: (response, variables) => {
            const savedNote = response.data

            queryClient.setQueryData(["notes"], (currentNotes = []) => [
                savedNote,
                ...currentNotes.filter((note) => note.id !== savedNote.id),
            ])

            if (variables.kind === "create") {
                setDraftNotes((currentDrafts) =>
                    currentDrafts.filter((draft) => draft.id !== variables.draftId)
                )
                setActiveDraft(null)
            } else {
                setPendingChanges((currentChanges) => {
                    const nextChanges = { ...currentChanges }
                    delete nextChanges[variables.id]
                    return nextChanges
                })
            }

            setSelectedNote(savedNote)
            setNoteTitle(savedNote.title || "Untitled")
            setNoteContent(savedNote.content || "")
            queryClient.invalidateQueries({ queryKey: ["notes"] })
        },
    })

    const deleteMutation = useMutation({
        mutationFn: (noteId) => notesApi.delete(noteId),
        onSuccess: (_, noteId) => {
            queryClient.setQueryData(["notes"], (currentNotes = []) =>
                currentNotes.filter((note) => note.id !== noteId)
            )
            setPendingChanges((currentChanges) => {
                const nextChanges = { ...currentChanges }
                delete nextChanges[noteId]
                return nextChanges
            })
            if (selectedNote?.id === noteId) {
                setSelectedNote(null)
                setNoteTitle("")
                setNoteContent("")
            }
            queryClient.invalidateQueries({ queryKey: ["notes"] })
        },
    })

    const handleSelectNote = (note) => {
        setSelectedNote(note)
        setActiveDraft(null)
        setNoteTitle(pendingChanges[note.id]?.title ?? note.title ?? "Untitled")
        setNoteContent(pendingChanges[note.id]?.content ?? note.content ?? "")
        setAiResponse(null)
    }

    const handleAddNote = () => {
        const existingTitles = new Set([
            ...(notes || []).map((note) =>
                (pendingChanges[note.id]?.title ?? note.title ?? "Untitled").toLowerCase()
            ),
            ...draftNotes.map((draft) => draft.title.toLowerCase()),
        ])
        let title = "Untitled"
        let suffix = 1
        while (existingTitles.has(title.toLowerCase())) {
            title = `Untitled(${suffix})`
            suffix += 1
        }

        const draft = {
            id: nextDraftId.current++,
            title,
            content: "",
            isDirty: false,
        }
        setDraftNotes((currentDrafts) => [draft, ...currentDrafts])
        setSelectedNote(null)
        setActiveDraft(draft)
        setNoteTitle(draft.title)
        setNoteContent("")
        setAiResponse(null)
    }

    const handleRename = (item, isDraft, title) => {
        const normalizedTitle = title.trim() || "Untitled"
        if (isDraft) {
            const updatedDraft = { ...item, title: normalizedTitle, isDirty: true }
            setDraftNotes((currentDrafts) => currentDrafts.map((draft) =>
                draft.id === item.id ? updatedDraft : draft
            ))
            if (activeDraft?.id === item.id) {
                setActiveDraft(updatedDraft)
                setNoteTitle(normalizedTitle)
            }
        } else {
            setPendingChanges((currentChanges) => ({
                ...currentChanges,
                [item.id]: { ...currentChanges[item.id], title: normalizedTitle },
            }))
            if (selectedNote?.id === item.id) setNoteTitle(normalizedTitle)
        }
        setRenamingItemId(null)
        setOpenSettingsId(null)
    }

    const handleTitleChange = (title) => {
        setNoteTitle(title)
        if (activeDraft) {
            const updatedDraft = { ...activeDraft, title, isDirty: true }
            setActiveDraft(updatedDraft)
            setDraftNotes((currentDrafts) => currentDrafts.map((draft) =>
                draft.id === updatedDraft.id ? updatedDraft : draft
            ))
        } else if (selectedNote) {
            setPendingChanges((currentChanges) => {
                const changes = { ...currentChanges[selectedNote.id], title }
                if (
                    title === (selectedNote.title || "Untitled")
                    && (changes.content ?? selectedNote.content ?? "") === (selectedNote.content ?? "")
                ) {
                    const nextChanges = { ...currentChanges }
                    delete nextChanges[selectedNote.id]
                    return nextChanges
                }
                return { ...currentChanges, [selectedNote.id]: changes }
            })
        }
    }

    const handleDelete = (note) => {
        if (!window.confirm("Are you sure you want to delete this note?")) return
        deleteMutation.mutate(note.id)
        setOpenSettingsId(null)
    }

    const handleDeleteDraft = (draft) => {
        if (!window.confirm("Are you sure you want to delete this note?")) return
        setDraftNotes((currentDrafts) => currentDrafts.filter((item) => item.id !== draft.id))
        if (activeDraft?.id === draft.id) {
            setActiveDraft(null)
            setNoteTitle("")
            setNoteContent("")
        }
        setOpenSettingsId(null)
    }

    const handleSelectDraft = (draft) => {
        setSelectedNote(null)
        setActiveDraft(draft)
        setNoteTitle(draft.title)
        setNoteContent(draft.content)
        setAiResponse(null)
    }

    const handleContentChange = (content) => {
        setNoteContent(content)
        if (activeDraft) {
            const updatedDraft = { ...activeDraft, content, isDirty: true }
            setActiveDraft(updatedDraft)
            setDraftNotes((currentDrafts) => currentDrafts.map((draft) =>
                draft.id === updatedDraft.id ? updatedDraft : draft
            ))
        } else if (selectedNote) {
            setPendingChanges((currentChanges) => {
                const noteChanges = {
                    ...currentChanges[selectedNote.id],
                    content,
                }
                const originalContent = selectedNote.content ?? ""

                if (
                    content === originalContent
                    && (noteChanges.title ?? selectedNote.title) === selectedNote.title
                ) {
                    const nextChanges = { ...currentChanges }
                    delete nextChanges[selectedNote.id]
                    return nextChanges
                }

                return { ...currentChanges, [selectedNote.id]: noteChanges }
            })
        }
    }

    const handleSave = () => {
        const data = {
            title: noteTitle.trim() || "Untitled",
            content: noteContent,
        }

        if (activeDraft) {
            saveMutation.mutate({ kind: "create", draftId: activeDraft.id, data })
        } else if (selectedNote) {
            saveMutation.mutate({ kind: "update", id: selectedNote.id, data })
        }
    }

    const isSelectedNoteDirty = selectedNote
        ? Boolean(pendingChanges[selectedNote.id])
        : Boolean(activeDraft?.isDirty)

    const handleAiAction = async (action) => {
        if (!selectedNote) return
        setAiLoading(true)
        setAiResponse(null)

        try {
            let response
            switch(action){
                case "summarize":
                    response = await aiApi.summarize(selectedNote.id, aiProvider)
                    break
                case "questions":
                    response = await aiApi.generateQuestions(selectedNote.id, aiProvider)
                    break
                case "enhance":
                    response = await aiApi.enhance(selectedNote.id, aiProvider)
                    break
                case "ask":
                    response = await aiApi.ask(aiQuestion, aiProvider)
                    break
            }
            setAiResponse(response.data)
        } catch (err) {
            setAiResponse({ error: err.response?.data?.detail || "AI request failed"})
        } finally {
            setAiLoading(false)
        }
    }

    const renderNoteRow = (item, isDraft = false) => {
        const itemId = `${isDraft ? "draft" : "note"}-${item.id}`
        const title = isDraft
            ? item.title || "Untitled"
            : pendingChanges[item.id]?.title ?? item.title ?? "Untitled"
        const isDirty = isDraft ? item.isDirty : Boolean(pendingChanges[item.id])
        const isSelected = isDraft
            ? activeDraft?.id === item.id
            : selectedNote?.id === item.id
        const visibleTitle = title.length > 12 ? `${title.slice(0, 12)}...` : title

        return (
            <div
                key={itemId}
                className={`relative mb-1 flex min-w-0 items-center rounded-lg text-sm transition-colors
                    ${isDirty || isDraft ? "bg-green-50 text-green-900" : "text-gray-700"}
                    ${isSelected ? "ring-1 ring-inset ring-blue-200" : ""}`}
            >
                {renamingItemId === itemId ? (
                    <form
                        className="flex min-w-0 flex-1 items-center gap-1 p-1"
                        onSubmit={(event) => {
                            event.preventDefault()
                            handleRename(item, isDraft, renameValue)
                        }}
                    >
                        <input
                            autoFocus
                            aria-label={`Rename ${title}`}
                            value={renameValue}
                            onChange={(event) => setRenameValue(event.target.value)}
                            onKeyDown={(event) => {
                                if (event.key === "Escape") setRenamingItemId(null)
                            }}
                            className="min-w-0 flex-1 rounded border border-gray-300 px-2 py-1 outline-none focus:border-blue-500"
                        />
                        <button type="submit" aria-label="Save title" className="px-1 text-blue-700">
                            Save
                        </button>
                    </form>
                ) : (
                    <>
                        <button
                            type="button"
                            title={title}
                            onClick={() => isDraft ? handleSelectDraft(item) : handleSelectNote(item)}
                            className="flex min-h-10 min-w-0 flex-1 items-center gap-2 overflow-hidden px-3 py-2 text-left hover:bg-black/5"
                        >
                            {isDirty && (
                                <span
                                    aria-label="Unsaved changes"
                                    title="Unsaved changes"
                                    className="h-2.5 w-2.5 shrink-0 rounded-full bg-green-500"
                                />
                            )}
                            <span className="min-w-0 truncate">{visibleTitle}</span>
                        </button>
                        <button
                            type="button"
                            aria-label={`Settings for ${title}`}
                            aria-expanded={openSettingsId === itemId}
                            onClick={() => setOpenSettingsId((current) => current === itemId ? null : itemId)}
                            className="grid h-9 w-9 shrink-0 place-items-center rounded hover:bg-black/10"
                        >
                            <span aria-hidden="true">⋮</span>
                        </button>
                        {openSettingsId === itemId && (
                            <div className="absolute right-1 top-full z-20 grid min-w-32 rounded-md border border-gray-200 bg-white p-1 shadow-lg">
                                <button
                                    type="button"
                                    onClick={() => {
                                        setRenameValue(title)
                                        setRenamingItemId(itemId)
                                    }}
                                    className="rounded px-3 py-2 text-left hover:bg-gray-100"
                                >
                                    Rename
                                </button>
                                <button
                                    type="button"
                                    onClick={() => isDraft ? handleDeleteDraft(item) : handleDelete(item)}
                                    className="rounded px-3 py-2 text-left text-red-700 hover:bg-red-50"
                                >
                                    {isDraft ? "Discard draft" : "Delete"}
                                </button>
                            </div>
                        )}
                    </>
                )}
            </div>
        )
    }

    return (
        <div className="flex flex-col h-screen bg-gray-50 overflow-hidden">
            <div className="grid grid-cols-3 items-center px-4 py-3 border-b border-gray-200 bg-white bg-blue">
                <h1 className="col-start-2 text-center text-lg font-bold text-gray-900">Notable</h1>
                {/* User Session Logout */}
                    {/* TODO: List of options: Profile, Logout 
                    <button
                        onClick={handleDropDown}
                    >
                        Caret Icon
                    </button>
                    */}
                <button
                    onClick={handleLogout}
                    className="justify-self-end text-sm text-gray-500 hover:text-red-500 transition-colors"
                >
                    Logout
                </button>
            </div>

            {/* Content row: sidebar | editor | AI Panel */}
            <div className="flex flex-1 overflow-hidden">

                {/* Sidebar | Notes Selection */}
                <div className="w-64 border-r border-gray-200 overflow-y-auto p-2">
                    <div className="flex flex-1 items-center border-b border-gray-200 mb-2 p-1.5">
                        <h2 className="text-md font-semibold text-gray-900 ">List</h2>
                        <button
                            onClick={handleAddNote}
                            disabled={saveMutation.isPending}
                            className=" ml-auto text-xl items-center rounded hover:bg-blue-100 transition-colors"
                        >
                            +
                        </button>
                    </div>

                    {isLoading ? (
                        <p className="text-sm text-gray-400 p-2">Loading notes...</p>
                    ) : (
                        <>
                            {draftNotes.map((draft) => renderNoteRow(draft, true))}
                            {notes?.map((note) => renderNoteRow(note))}
                        </>
                    )}

                </div>

                {/* Note Editor */}
                <div className="flex-1 flex flex-col overflow-hidden">
                    <div className="p-4 border-b border-gray-200 bg-white flex justify-between items-center">
                        <div className="flex min-w-0 flex-1 items-center gap-2">
                            {isSelectedNoteDirty && !isEditingTitle && (
                                <span
                                    aria-label="Unsaved changes"
                                    title="Unsaved changes"
                                    className="h-2.5 w-2.5 shrink-0 rounded-full bg-green-500"
                                />
                            )}
                            {isEditingTitle && (selectedNote || activeDraft) ? (
                                <input
                                    autoFocus
                                    aria-label="Edit note title"
                                    value={noteTitle}
                                    onChange={(event) => handleTitleChange(event.target.value)}
                                    onBlur={() => setIsEditingTitle(false)}
                                    onKeyDown={(event) => {
                                        if (event.key === "Enter") setIsEditingTitle(false)
                                        if (event.key === "Escape") {
                                            handleTitleChange(renameValue)
                                            setIsEditingTitle(false)
                                        }
                                    }}
                                    style={{ width: "min(50%, 25ch)", maxWidth: "min(50%, 25ch)" }}
                                    className="min-w-0 flex-none rounded border border-gray-300 px-2 py-1 text-sm font-medium text-gray-700 outline-none focus:border-blue-500"
                                />
                            ) : (
                                <h2
                                    onDoubleClick={() => {
                                        if (!selectedNote && !activeDraft) return
                                        setRenameValue(noteTitle)
                                        setIsEditingTitle(true)
                                    }}
                                    title={(selectedNote || activeDraft) ? "Double-click to rename" : undefined}
                                    className="flex min-w-0 flex-1 cursor-text items-center gap-2 text-sm font-medium text-gray-600"
                                >
                                    {selectedNote || activeDraft
                                        ? (noteTitle || "Untitled").length > 25
                                            ? `${(noteTitle || "Untitled").slice(0, 25)}...`
                                            : noteTitle || "Untitled"
                                        : "Select a note"}
                                </h2>
                            )}
                        </div>
                        <button
                            onClick={handleSave}
                            disabled={
                                (!selectedNote && !activeDraft)
                                || (!activeDraft && !isSelectedNoteDirty)
                                || saveMutation.isPending
                            }
                            className="bg-blue-600 text-white text-sm px-4 py-1.5 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                        >
                            {saveMutation.isPending ? "Saving..." : "Save"}
                        </button>
                    </div>

                    {saveMutation.isError && (
                        <p role="alert" className="px-4 pt-3 text-sm text-red-600">
                            {saveMutation.error?.response?.data?.detail || "Could not save note. Please try again."}
                        </p>
                    )}

                    <textarea
                        value={noteContent}
                        onChange={(e) => handleContentChange(e.target.value)}
                        placeholder="Start writing your note..."
                        disabled={!selectedNote && !activeDraft}
                        className="flex-1 p-6 resize-none text-gray-800 text-sm leading-relaxed focus:outline-none bg-transparent disabled:opacity-40"
                    />
                </div>

                {/*AI Panel*/}
                <div className="w-80 bg-white border-1 border-gray-200 flex flex-col">
                    <div className="p-4 border-b border-gray-200">
                        <h2 className="text-sm font-semibold text-gray-900 mb-2">AI Assistant</h2>
                        {/*AI Provider Switcher */}
                        <select
                            value={aiProvider}
                            onChange={(e) => setaiProvider(e.target.value)}
                            className="w-full text-xs border border-gray-200 rounder-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            <option value="gemini">Gemini</option>
                            <option value="huggingface">Hugging Face</option>
                        </select>
                    </div>
                    {/*AI Action Buttons*/}
                    <div className="p-4 border-b border-gray-200 flex flex-col gap-2">
                        {["summarize", "questions", "enhance"].map(action => (
                            <button
                                key={action}
                                onClick={() => handleAiAction(action)}
                                disabled={!selectedNote || aiLoading}
                                className="w-full text-left text-sm px-3 py-2 rounded-lg border border-gray-200 hover:bg-gray-50 disabled:opacity-40 transition-colors capitalize"
                            >
                                {action === "summarize" && "📝 Summarize note"}
                                {action === "questions" && "❓ Generate questions"}
                                {action === "enhance" && "✨ Enhance note"}
                            </button>
                        ))}
                    </div>
                    {/* AI Search / Ask */}
                    <div className="mt-1 p-4 border-b border-gray-200">
                        <p className="text-xs text-gray-500 mb-2">Ask AI about your notes</p>
                        <div className="flex gap-2">
                            <input 
                                type="text"
                                value={aiQuestion}
                                onChange={(e) => setAiQuestion(e.target.value)}
                                placeholder="Ask anything..."
                                className="flex-1 text-xs border border-gray-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                            <button
                                onClick={() => handleAiAction("ask")}
                                disabled={!aiQuestion || aiLoading}
                                className="bg-blue-600 text-white text-xs px-3 py-1.5 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                            >
                                Ask
                            </button>
                        </div>
                    </div>
                    {/* AI Response */}
                    <div className="flex-1 overflow-y-auto p-4">
                        {aiLoading && (
                            <div className="text-sm text-gray-400 text-center mt-4">
                                Thinking...
                            </div>
                        )}
                        {aiResponse && !aiLoading && (
                            <div className={`text-sm rounded-lg p-3 leading-relaxed
                                ${aiResponse.error
                                    ? "bg-red-50 text-red-600"
                                    : "bg-blue-50 text-gray-700"
                                }`}
                            >
                                {aiResponse.error || aiResponse.result}
                            </div>
                        )}
                        {!aiResponse && !aiLoading && (
                            <p className="text-xs text-gray-400 text-center mt-4">
                                Select a note and choose an AI action
                            </p>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}