import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { MetadataContext, MetadataProvider } from '../../../context/MetadataContext';
import Login from '../Login';
import { createMockMetadataContext } from '../../../utils/testUtils';

// Create a wrapper component with necessary context and routing
const renderWithContextAndRouter = (ui, contextValue = createMockMetadataContext()) => {
  return render(
    <MetadataContext.Provider value={contextValue}>
      <MemoryRouter initialEntries={['/login']}>
        <Routes>
          <Route path="/login" element={ui} />
          <Route path="/" element={<div>Home Page</div>} />
        </Routes>
      </MemoryRouter>
    </MetadataContext.Provider>
  );
};

describe('Login Component', () => {
  test('renders login form', () => {
    renderWithContextAndRouter(<Login />);
    
    // Check if important elements are rendered
    expect(screen.getByText(/Log In to Videntify/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Email Address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Log In/i })).toBeInTheDocument();
  });
  
  test('shows validation error when fields are empty', async () => {
    renderWithContextAndRouter(<Login />);
    
    // Submit form without filling fields
    fireEvent.click(screen.getByRole('button', { name: /Log In/i }));
    
    // Check for validation error
    await waitFor(() => {
      expect(screen.getByText(/Please enter both email and password/i)).toBeInTheDocument();
    });
  });
  
  test('calls login function with correct values on submit', async () => {
    const mockContextValue = createMockMetadataContext();
    renderWithContextAndRouter(<Login />, mockContextValue);
    
    // Fill form fields
    fireEvent.change(screen.getByLabelText(/Email Address/i), {
      target: { value: 'test@example.com' }
    });
    
    fireEvent.change(screen.getByLabelText(/Password/i), {
      target: { value: 'password123' }
    });
    
    // Check remember me checkbox
    fireEvent.click(screen.getByLabelText(/Remember me/i));
    
    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /Log In/i }));
    
    // Check if login function was called with correct values
    await waitFor(() => {
      expect(mockContextValue.login).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123',
        rememberMe: true
      });
    });
  });
  
  test('redirects user when already authenticated', async () => {
    const mockContextValue = {
      ...createMockMetadataContext(),
      isAuthenticated: true
    };
    
    renderWithContextAndRouter(<Login />, mockContextValue);
    
    // Check if redirected to home page
    await waitFor(() => {
      expect(screen.getByText(/Home Page/i)).toBeInTheDocument();
    });
  });
  
  test('displays error message when login fails', async () => {
    const mockContextValue = {
      ...createMockMetadataContext(),
      login: jest.fn().mockResolvedValue(false),
      authError: 'Invalid credentials'
    };
    
    renderWithContextAndRouter(<Login />, mockContextValue);
    
    // Fill form fields
    fireEvent.change(screen.getByLabelText(/Email Address/i), {
      target: { value: 'test@example.com' }
    });
    
    fireEvent.change(screen.getByLabelText(/Password/i), {
      target: { value: 'wrongpassword' }
    });
    
    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /Log In/i }));
    
    // Check if error message is displayed
    await waitFor(() => {
      expect(screen.getByText(/Invalid credentials/i)).toBeInTheDocument();
    });
  });
});
