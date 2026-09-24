import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/api';

export default function Login() {
  const [user, setUser] = useState("")
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(false);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)

    const loginCredentials = user.includes("@")
      ? { email: user, password }
      : { username: user, password }

    try {
      const res = await api.post("/auth/login", loginCredentials)
      console.log("Login success:", res.data);
      navigate("/dashboard");
    } catch (err) {
      console.error("Login failed:", err.response?.data || err.message);
    } finally {
    setLoading(false)
    }
  }

  const handleOAuth = (provider) => {
    // Redirect to FastAPI OAuth endpoint
    window.location.href = import.meta.env.VITE_API_URL + provider;
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      {/* Smooth Spinning Tailwind Icon */}
      {loading && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 transition-opacity">
          <div className="bg-white p-6 rounded-xl shadow-2xl flex flex-col items-center max-w-xs w-full border border-gray-100 animate-fade-in">
            <svg className="animate-spin h-10 w-10 text-blue-600 mb-4" xmlns="http://w3.org" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <p className="text-gray-700 font-medium tracking-wide">Signing in...</p>
            <p className="text-gray-400 text-xs mt-1">Please wait a moment.</p>
          </div>
        </div>
      )}

      <div className="bg-white shadow-lg rounded-lg w-full max-w-sm p-6">
        <h1 className="text-2xl font-bold text-center mb-6">Notable</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* User ID / Email */}
          <div>
            <label className="block text-sm font-medium text-gray-700">
              User ID / Email
            </label>
            <input
              type="text"
              value={user}
              onChange={(e) => setUser(e.target.value)}
              className="mt-1 block w-full border border-gray-300 rounded-md p-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="myusername / you@example.com"
              required
            />
          </div>

          {/* Password */}
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 block w-full border border-gray-300 rounded-md p-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="••••••••"
              required
            />
          </div>

          {/* Remember Me */}
          <div className="flex items-center">
            <input
              id="remember"
              type="checkbox"
              checked={remember}
              onChange={(e) => setRemember(e.target.checked)}
              className="h-4 w-4 text-blue-600 border-gray-300 rounded"
            />
            <label htmlFor="remember" className="ml-2 text-sm text-gray-600">
              Remember me
            </label>
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md font-semibold hover:bg-blue-700 transition"
          >
            {loading ? "Signing in..." : "Submit"}
          </button>
        </form>

        {/* OAuth Buttons */}
        <div className="mt-6 space-y-2">
          <button
            onClick={() => handleOAuth("/google")}
            className="w-full bg-red-500 text-white py-2 px-4 rounded-md font-semibold hover:bg-red-600 transition"
          >
            Continue with Google
          </button>
          <button
            onClick={() => handleOAuth("/github")}
            className="w-full bg-gray-800 text-white py-2 px-4 rounded-md font-semibold hover:bg-gray-900 transition"
          >
            Continue with GitHub
          </button>
        </div>

        {/* Register Link */}
        <p className="mt-4 text-center text-sm text-gray-600">
          Don’t have an account?{" "}
          <a href="/register" className="text-blue-600 hover:underline">
            Register
          </a>
        </p>
      </div>
    </div>
  );
}
