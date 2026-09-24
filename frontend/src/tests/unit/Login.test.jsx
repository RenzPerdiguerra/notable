import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter } from "react-router-dom"
import { afterEach, expect, vi } from "vitest"
import Login from "../../pages/Login"
import api from "../../api/api"


afterEach(() => {
    vi.restoreAllMocks()
})

// Wrapper for Login useNavigate
const renderLogin = () => render(
    <MemoryRouter>
        <Login />
    </MemoryRouter>
)
// -- Unit Test --
describe("Login Page", () => {
    // Render check
    it("renders login form correctly", () => {
        renderLogin()

        expect(screen.getByText("Notable")).toBeInTheDocument()
        expect(screen.getByPlaceholderText("myusername / you@example.com")).toBeInTheDocument()
        expect(screen.getByPlaceholderText("••••••••")).toBeInTheDocument()
        expect(screen.getByRole("button", { name: "Submit" })).toBeInTheDocument()
    })

    // Input fields
    it("updates username field when user types", async () => {
        renderLogin()
        const user = userEvent.setup()

        const usernameInput = screen.getByPlaceholderText("myusername / you@example.com")
        await user.type(usernameInput, "testuser")
        
        expect(usernameInput).toHaveValue("testuser")
    })
    // Checkbox responds when user clicks
    it("checks the checkbox when Remember Me is clicked", async () => {
        renderLogin()
        const user = userEvent.setup()

        const checkbox = screen.getByRole("checkbox", { name: "Remember me"})
        await user.click(checkbox)

        expect(checkbox).toBeChecked()
    })
    // Buttons disabling while loading
    it("disables submit button while loading", async () => {
        vi.spyOn(api, "post").mockReturnValue(new Promise(() => {}))
        renderLogin()
        const user = userEvent.setup()

        await user.type(screen.getByPlaceholderText("myusername / you@example.com"), "testuser")
        await user.type(screen.getByPlaceholderText("••••••••"), "password123")
        const button = screen.getByRole("button", { name: "Submit"})
        await user.click(button)
        // Button should show loading state
        const loadingButton = await screen.findByRole("button", { name: "Signing in..." })
        expect(loadingButton).toBeDisabled()
        expect(api.post).toHaveBeenCalledWith("/auth/login", {
            username: "testuser",
            password: "password123",
        })
    })
    // Register modal prompt
    it("opens register modal when Register is clicked", async () => {
        renderLogin()
        const user = userEvent.setup()

        expect(screen.getByRole("link", { name: "Register" })).toHaveAttribute("href", "/register")
    })
})

