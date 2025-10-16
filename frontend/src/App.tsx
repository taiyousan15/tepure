import { BrowserRouter, Routes, Route, Link, useNavigate } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Templates from './pages/Templates'
import CreateTemplate from './pages/CreateTemplate'
import UseTemplate from './pages/UseTemplate'
import TestDashboard from './pages/TestDashboard'
import Login from './pages/Login'
import PrivateRoute from './components/PrivateRoute'
import { isAuthenticated, logout, getUser } from './utils/auth'

function Navigation() {
  const navigate = useNavigate();
  const user = getUser();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (!isAuthenticated()) {
    return null;
  }

  return (
    <nav className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <Link to="/" className="text-xl font-bold text-gray-900">
                Figma Template Automation
              </Link>
            </div>
            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
              <Link
                to="/"
                className="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
              >
                ダッシュボード
              </Link>
              <Link
                to="/templates"
                className="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
              >
                テンプレート
              </Link>
            </div>
          </div>
          <div className="flex items-center">
            <span className="text-sm text-gray-700 mr-4">{user?.email}</span>
            <button
              onClick={handleLogout}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              ログアウト
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <Navigation />

        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route
              path="/"
              element={
                <PrivateRoute>
                  <Dashboard />
                </PrivateRoute>
              }
            />
            <Route
              path="/templates"
              element={
                <PrivateRoute>
                  <Templates />
                </PrivateRoute>
              }
            />
            <Route
              path="/templates/create"
              element={
                <PrivateRoute>
                  <CreateTemplate />
                </PrivateRoute>
              }
            />
            <Route
              path="/templates/:templateId/use"
              element={
                <PrivateRoute>
                  <UseTemplate />
                </PrivateRoute>
              }
            />
            <Route
              path="/test"
              element={<TestDashboard />}
            />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App
