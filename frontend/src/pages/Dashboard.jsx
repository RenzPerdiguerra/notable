import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { aiApi, notesApi } from '../api/api';


export default function Dashboard() {
    const [selectedNote, setSelectedNote] = useState("")
    const [noteContent, setNoteContent] = useState("")
    const [aiQuestion, setAiQuestion] = useState("")
    const [aiResponse, setAiResponse] = useState("")
    const [aiLoading, setAiLoading] = useState("")
    const [aiProvider, setaiProvider] = useState("")
    const navigate = useNavigate()
    const queryClient = useQueryClient()

    const { data: notes, isLoading} = useQuery({
        queryKey: ["notes"],
        queryFn: () => notesApi.getAll().then(r => r.data)
    })

    const saveMutation = useMutation({
        mutationFn: (data) => selectedNote
            ? notesApi.update(selectedNote.id, data)
            : notesApi.create(data),
        onSuccess: () => {
            queryClient.invalidateQueries(["notes"])
        }
    })

    const handleSelectNote = (note) => {
        setSelectedNote(note)
        setNoteContent(note.content)
        setAiResponse(null)
    }

    // TODO: Fill with process for logout
    const handleLogout = () => {
        navigate("/login")
    }

    /* TODO: handleDropDown */

    const handleSave = () => {
        if (!selectedNote) return
        saveMutation.mutate({ content: noteContent })
    }

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

    return (
        <div className="flex h-screen bg-gray-50 overflow-hidden">
            <div className="p-4 border-b border-gray-200">
                <h1 className="text-lg font-bold text-gray-900">Notable</h1>
            </div>

            <div className="flex-1 overflow-y-auto p-2">
                {isLoading ? (
                    <p className="text-sm text-gray-400 p-2">Loading notes...</p>
                ) : (
                    notes?.map(note => (
                        <button
                            key={note.id}
                            onClick={() => handleSelectNote(note)}
                            className={`w-full text-left px-3 py-2 rounded-lg text-sm mb-1 transition-colors
                                ${selectedNote?.id === note.id
                                    ? `bg-blue-50 text-blue-700 font-medium`
                                    : 'text-gray-700 hover:bg-gray-100' 
                                }`}
                        >
                            {note.title || 'Untitled'}
                        </button>
                    ))
                )}
            </div>

            {/* User Session Logout */}
            <div className="dropdown p-4 border-t border-gray-200">
                 {/* TODO: List of options: Profile, Logout 
                <button
                    onClick={handleDropDown}
                >
                    Caret Icon
                </button>
                */}
                <button
                    onClick={handleLogout}
                    className="w-full text-sm text-gray-500 hover:text-red-500 transition-colors"
                >
                    Logout
                </button>
            </div>

            {/*Note Editor*/}
            <div className="flex-1 flex flex-col overflow-hidden">
                <div className="p-4 border-b border-gray-200 bg-white flex justify-between items-center">
                    <h2 className="text-sm font-medium text-gray-600">
                        {selectedNote ? selectedNote.title || "Untitled" : "Select a note"}
                    </h2>
                    <button
                        onClick={handleSave}
                        disabled={!selectedNote || saveMutation.isPending}
                        className="bg-blue-600 text-white text-sm px-4 py-1.5 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                    >
                        {saveMutation.isPending ? "Saving..." : "Save"}
                    </button>
                </div>

                <textarea
                    value={noteContent}
                    onChange={(e) => setNoteContent(e.target.value)}
                    placeholder="Start writing your note..."
                    disabled={!selectedNote}
                    className="flex-1 p-6 resize-none text-gray-800 text-sm leading-relaxed focus:outline-none bg-transparent disabled:opacity-40"
                />
            </div>

            {/*AI Panel*/}
            <div className="w-80 bg-white border-1 border-gray-200 flex flex-col" >
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
    );
}