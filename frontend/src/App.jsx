import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { authApi } from './api/api';
import Login from './pages/Login'
import Register from './pages/Register';
import Dashboard from './pages/Dashboard'
import NotFound from './pages/NotFound'
import './App.css'


const ProtectedRoute = ({ children }) => {
    const [isAuth, setIsAuth] = useState(null);

    useEffect(() => {
      authApi.me()
        .then(() => setIsAuth(true))
        .catch(() =>setIsAuth(false));
    }, []);
    
    if (isAuth === null) return <div>Loading...</div>;
    return isAuth ? children : <Navigate to="/login" />;
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/login" />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/dashboard" element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        } />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App