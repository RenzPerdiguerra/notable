import setUpServer from "msw/node"
import { http, HttpResponse } from "msw"

export const handlers = [
    // Auth
    http.post("http://127.0.0.1:8000/auth/login", () => {
        return HttpResponse.json({
            access_token: "fake-jwt-token-for-testing",
            token_type: "bearer"
        })
    }),

    http.get("http://127.0.0.1:8000/users/me", () => {
        return HttpResponse.json({
            id: 1,
            username: "testuser",
            email: "test@example.com",
            role: "user",
        })
    }),

    http.post("http://127.0.0.1:8000/auth/register", () => {
        return HttpResponse.json({
            id: 1,
            email: "test@example.com",
            username: "testuser",
        }, { status: 200 })
    }),

    // Notes
    http.get("http://127.0.0.1/notes", () => {
        return HttpResponse.json([
            { note_id: 1, title: "First Note", content: "My darling"},
            { note_id: 2, title: "Second Note", content: "My tower of refuge"}
        ])
    }),

    http.post("http://127.0.0.1:8000/notes/", () => {
        return HttpResponse.json({
            note_id: 3,
            title: "Third Note",
            content: "My Baby",
        }, { status: 201 })
    }),
]

// Runs the fake server
export const server = setUpServer(...handlers)