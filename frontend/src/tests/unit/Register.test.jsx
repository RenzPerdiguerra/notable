import { MemoryRouter } from "react-router-dom"
import { screen, render } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { vi } from "vitest"
import Register from "../../pages/Register"

const mockOnClose = vi.fn()

const renderRegister = () => render(
    <MemoryRouter>
        <Register onClose={mockOnClose} />
    </MemoryRouter>
)

describe("Register modal", () => {
    // Renders all fields
    it("renders all form fields", () => {
        renderRegister()

        expect(screen.getByPlaceholderText("you@example.com")).toBeInTheDocument()
        expect(screen.getByPlaceholderText("username")).toBeInTheDocument()
        expect(screen.getByPlaceholderText("Min. 6 characters")).toBeInTheDocument()
        expect(screen.getByPlaceholderText("Repeat your password")).toBeInTheDocument()
    })
    // Password mismatch shows error
    it("shows error when passwords do not match", async () => {
        renderRegister()
        const user = userEvent.setup()

        await user.type(screen.getByPlaceholderText("you@example.com"), "test@example.com")
        await user.type(screen.getByPlaceholderText("username"), "testuser")
        await user.type(screen.getByPlaceholderText("Min. 6 characters"), "password123")
        await user.type(screen.getByPlaceholderText("Repeat your password"), "diff_password")
        await user.click(screen.getByRole("button", { name: "Create account"}))

        expect(screen.getByText("Passwords do not match")).toBeInTheDocument()
    })
    // Password length is short error
    it("shows error when passwords length is less than 6 characters", async () => {
        renderRegister()
        const user = userEvent.setup()

        await user.type(screen.getByPlaceholderText("you@example.com"), "test@example.com")
        await user.type(screen.getByPlaceholderText("username"), "testuser")
        await user.type(screen.getByPlaceholderText("Min. 6 characters"), "pass1")
        await user.type(screen.getByPlaceholderText("Repeat your password"), "pass1")
        await user.click(screen.getByRole("button", { name: "Create account"}))

        expect(screen.getByText("Password must be at least 6 characters")).toBeInTheDocument()
    })
    // Close button applies
    it("calls onClose when close button is clicked", async () => {
        renderRegister()
        const user = userEvent.setup()

        await user.click(screen.getByText("X"))
        expect(mockOnClose).toHaveBeenCalled()
    })
    // Oauth buttons render
    it("renders Google and Github Oauth buttons", () => {
        renderRegister()

        expect(screen.getByRole("button", { name: "Continue with Google"})).toBeInTheDocument()
        expect(screen.getByRole("button", { name: "Continue with GitHub"})).toBeInTheDocument()
    })
})