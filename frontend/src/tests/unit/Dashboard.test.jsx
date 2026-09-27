import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, expect, it, vi } from "vitest"
import { MemoryRouter } from "react-router-dom"
import Dashboard from "../../pages/Dashboard"
import { notesApi } from "../../api/api"

const savedNote = {
    id: 7,
    title: "Saved note",
    content: "Original content",
}

const renderDashboard = () => {
    const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
    })

    return render(
        <QueryClientProvider client={queryClient}>
            <MemoryRouter>
                <Dashboard />
            </MemoryRouter>
        </QueryClientProvider>
    )
}

afterEach(() => {
    vi.restoreAllMocks()
})

it("keeps a saved note's edits pending when plus starts a new draft", async () => {
    vi.spyOn(notesApi, "getAll").mockResolvedValue({ data: [savedNote] })
    vi.spyOn(notesApi, "update").mockResolvedValue({
        data: { ...savedNote, content: "Edited content" },
    })
    const user = userEvent.setup()
    renderDashboard()

    await user.click(await screen.findByTitle("Saved note"))
    const editor = screen.getByPlaceholderText("Start writing your note...")
    await user.clear(editor)
    await user.type(editor, "Edited content")

    expect(screen.getAllByTitle("Unsaved changes")).toHaveLength(2)

    await user.click(screen.getByRole("button", { name: "+" }))
    expect(editor).toHaveValue("")
    expect(screen.getAllByTitle("Unsaved changes")).toHaveLength(1)

    await user.click(screen.getByTitle("Saved note"))
    expect(editor).toHaveValue("Edited content")
    await user.click(screen.getByRole("button", { name: "Save" }))

    await waitFor(() => {
        expect(notesApi.update).toHaveBeenCalledWith(7, {
            title: "Saved note",
            content: "Edited content",
        })
        expect(screen.getByTitle("Saved note").querySelector('[title="Unsaved changes"]')).toBeNull()
    })
})

it("creates a draft when Save is clicked", async () => {
    vi.spyOn(notesApi, "getAll").mockResolvedValue({ data: [] })
    vi.spyOn(notesApi, "create").mockResolvedValue({
        data: { id: 8, title: "Untitled", content: "New note content" },
    })
    const user = userEvent.setup()
    renderDashboard()

    await user.click(screen.getByRole("button", { name: "+" }))
    const editor = screen.getByPlaceholderText("Start writing your note...")
    await user.type(editor, "New note content")
    await user.click(screen.getByRole("button", { name: "Save" }))

    await waitFor(() => {
        expect(notesApi.create).toHaveBeenCalledWith({
            title: "Untitled",
            content: "New note content",
        })
        expect(screen.queryByTitle("Unsaved changes")).not.toBeInTheDocument()
    })
})

it("increments Untitled draft names when existing titles are present", async () => {
    vi.spyOn(notesApi, "getAll").mockResolvedValue({
        data: [{ ...savedNote, title: "Untitled" }],
    })
    const user = userEvent.setup()
    renderDashboard()

    await user.click(screen.getByRole("button", { name: "+" }))
    expect(screen.getByTitle("Untitled(1)")).toBeInTheDocument()
    await user.click(screen.getByRole("button", { name: "+" }))
    expect(screen.getByTitle("Untitled(2)")).toBeInTheDocument()
})

it("renames a saved note from the row settings menu and confirms deletion", async () => {
    vi.spyOn(notesApi, "getAll").mockResolvedValue({ data: [savedNote] })
    vi.spyOn(notesApi, "delete").mockResolvedValue({ data: null })
    vi.spyOn(window, "confirm").mockReturnValue(true)
    const user = userEvent.setup()
    renderDashboard()

    await user.click(await screen.findByRole("button", { name: "Settings for Saved note" }))
    await user.click(screen.getByRole("button", { name: "Rename" }))
    const renameInput = screen.getByRole("textbox", { name: "Rename Saved note" })
    await user.clear(renameInput)
    await user.type(renameInput, "Renamed note")
    await user.click(screen.getByRole("button", { name: "Save title" }))

    expect(screen.getByTitle("Renamed note")).toBeInTheDocument()
    expect(screen.getByTitle("Renamed note").querySelector('[title="Unsaved changes"]')).toBeInTheDocument()

    await user.click(screen.getByRole("button", { name: "Settings for Renamed note" }))
    await user.click(screen.getByRole("button", { name: "Delete" }))

    expect(window.confirm).toHaveBeenCalledWith("Are you sure you want to delete this note?")
    await waitFor(() => expect(notesApi.delete).toHaveBeenCalledWith(7))
})

it("renames the selected note by double-clicking its editor title", async () => {
    vi.spyOn(notesApi, "getAll").mockResolvedValue({ data: [savedNote] })
    vi.spyOn(notesApi, "update").mockResolvedValue({
        data: { ...savedNote, title: "Editor renamed note" },
    })
    const user = userEvent.setup()
    renderDashboard()

    await user.click(await screen.findByTitle("Saved note"))
    const editor = screen.getByPlaceholderText("Start writing your note...")
    const editorToolbar = screen.getByRole("button", { name: "Save" }).parentElement
    await user.clear(editor)
    await user.type(editor, "Edited content")
    expect(editorToolbar.querySelector('[title="Unsaved changes"]')).toBeInTheDocument()

    await user.dblClick(screen.getByRole("heading", { name: "Saved note" }))
    const titleInput = screen.getByRole("textbox", { name: "Edit note title" })
    expect(titleInput.style.width).toBe("min(50%, 25ch)")
    expect(editorToolbar.querySelector('[title="Unsaved changes"]')).toBeNull()
    expect(screen.getAllByTitle("Unsaved changes")).toHaveLength(1)
    await user.clear(titleInput)
    await user.type(titleInput, "Editor renamed note")
    await user.keyboard("{Enter}")

    expect(screen.getByRole("heading", { name: /Editor renamed note/ })).toBeInTheDocument()
    expect(editorToolbar.querySelector('[title="Unsaved changes"]')).toBeInTheDocument()
    await user.click(screen.getByRole("button", { name: "Save" }))
    await waitFor(() => {
        expect(notesApi.update).toHaveBeenCalledWith(7, {
            title: "Editor renamed note",
            content: "Edited content",
        })
    })
})
