import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { MetadataProvider } from './context/MetadataContext';

// Layout Components
import MainLayout from './components/layout/MainLayout';

// Page Components
import HomePage from './pages/HomePage';
import SearchPage from './pages/SearchPage';
import ResultsPage from './pages/ResultsPage';
import LibraryPage from './pages/LibraryPage';
import ProfilePage from './pages/ProfilePage';
import SettingsPage from './pages/SettingsPage';

// Auth Components
import Login from './components/auth/Login';
import SignUp from './components/auth/SignUp';

// Other Components
import NotFoundPage from './pages/NotFoundPage';

import './styles/global.css';

const App = () => {
  return (
    <Router>
      <MetadataProvider>
        <Routes>
          {/* Auth Routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<SignUp />} />
          
          {/* Main Layout Routes */}
          <Route element={<MainLayout />}>
            <Route path="/" element={<HomePage />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/results/:queryId" element={<ResultsPage />} />
            <Route path="/library" element={<LibraryPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/settings" element={<SettingsPage />} />
            
            {/* Add more routes as needed */}
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </MetadataProvider>
    </Router>
  );
};

export default App;
