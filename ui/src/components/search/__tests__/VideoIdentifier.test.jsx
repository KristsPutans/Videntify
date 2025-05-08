import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { MetadataContext } from '../../../context/MetadataContext';
import VideoIdentifier from '../VideoIdentifier';
import { createMockMetadataContext } from '../../../utils/testUtils';
import { identifyAPI } from '../../../services/api';

// Mock the API module
jest.mock('../../../services/api', () => ({
  identifyAPI: {
    identifyFile: jest.fn().mockResolvedValue({ data: { query_id: 'test-query-123' } }),
    identifyUrl: jest.fn().mockResolvedValue({ data: { query_id: 'test-query-123' } })
  }
}));

// Mock useNavigate from react-router-dom
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate
}));

// Create a wrapper component with necessary context and routing
const renderWithContextAndRouter = (ui, contextValue = createMockMetadataContext()) => {
  return render(
    <MetadataContext.Provider value={contextValue}>
      <MemoryRouter initialEntries={['/search']}>
        <Routes>
          <Route path="/search" element={ui} />
          <Route path="/results/:queryId" element={<div>Results Page</div>} />
        </Routes>
      </MemoryRouter>
    </MetadataContext.Provider>
  );
};

// Create a mock file for testing
const createMockFile = () => {
  const file = new File(['dummy content'], 'test-video.mp4', { type: 'video/mp4' });
  return file;
};

describe('VideoIdentifier Component', () => {
  beforeEach(() => {
    // Reset all mocks before each test
    jest.clearAllMocks();
  });

  test('renders video identifier component with tabs', () => {
    renderWithContextAndRouter(<VideoIdentifier />);
    
    // Check if important elements are rendered
    expect(screen.getByText(/Identify Your Video/i)).toBeInTheDocument();
    expect(screen.getByText(/Upload File/i)).toBeInTheDocument();
    expect(screen.getByText(/Video URL/i)).toBeInTheDocument();
  });
  
  test('allows switching between file upload and URL input tabs', () => {
    renderWithContextAndRouter(<VideoIdentifier />);
    
    // Initially, file upload area should be visible
    expect(screen.getByText(/Drag and drop your video file here/i)).toBeInTheDocument();
    
    // Click on URL tab
    fireEvent.click(screen.getByText(/Video URL/i));
    
    // URL input area should now be visible
    expect(screen.getByPlaceholderText(/Enter video URL here/i)).toBeInTheDocument();
    
    // Switch back to file tab
    fireEvent.click(screen.getByText(/Upload File/i));
    
    // File upload area should be visible again
    expect(screen.getByText(/Drag and drop your video file here/i)).toBeInTheDocument();
  });
  
  test('handles file selection', async () => {
    renderWithContextAndRouter(<VideoIdentifier />);
    
    // Create a mock file and simulate file selection
    const file = createMockFile();
    const fileInput = screen.getByTestId('file-input');
    
    // Simulate file selection
    Object.defineProperty(fileInput, 'files', {
      value: [file]
    });
    
    fireEvent.change(fileInput);
    
    // Check if file is displayed in the selected file area
    await waitFor(() => {
      expect(screen.getByText('test-video.mp4')).toBeInTheDocument();
    });
  });
  
  test('allows removing a selected file', async () => {
    renderWithContextAndRouter(<VideoIdentifier />);
    
    // Create a mock file and simulate file selection
    const file = createMockFile();
    const fileInput = screen.getByTestId('file-input');
    
    // Simulate file selection
    Object.defineProperty(fileInput, 'files', {
      value: [file]
    });
    
    fireEvent.change(fileInput);
    
    // Wait for file to be displayed
    await waitFor(() => {
      expect(screen.getByText('test-video.mp4')).toBeInTheDocument();
    });
    
    // Click remove button
    const removeButton = screen.getByRole('button', { name: /remove/i });
    fireEvent.click(removeButton);
    
    // Check if file was removed
    await waitFor(() => {
      expect(screen.queryByText('test-video.mp4')).not.toBeInTheDocument();
    });
  });
  
  test('submits file for identification and redirects to results', async () => {
    // Reset our mockNavigate before the test
    mockNavigate.mockReset();
    
    renderWithContextAndRouter(<VideoIdentifier />);
    
    // Create a mock file and simulate file selection
    const file = createMockFile();
    const fileInput = screen.getByTestId('file-input');
    
    // Simulate file selection
    Object.defineProperty(fileInput, 'files', {
      value: [file]
    });
    
    fireEvent.change(fileInput);
    
    // Wait for file to be displayed
    await waitFor(() => {
      expect(screen.getByText('test-video.mp4')).toBeInTheDocument();
    });
    
    // Click identify button
    const identifyButton = screen.getByRole('button', { name: /identify video/i });
    fireEvent.click(identifyButton);
    
    // Check if identifyFile was called
    await waitFor(() => {
      expect(identifyAPI.identifyFile).toHaveBeenCalled();
      // Check navigation to results page
      expect(mockNavigate).toHaveBeenCalledWith('/results/test-query-123');
    });
  });
  
  test('validates and submits URL for identification', async () => {
    // Reset our mockNavigate before the test
    mockNavigate.mockReset();
    
    renderWithContextAndRouter(<VideoIdentifier />);
    
    // Switch to URL tab
    fireEvent.click(screen.getByText(/Video URL/i));
    
    // Enter URL
    const urlInput = screen.getByPlaceholderText(/https:\/\/www\.youtube\.com\/watch\?v=\.\.\./i);
    fireEvent.change(urlInput, {
      target: { value: 'https://example.com/video.mp4' }
    });
    
    // Click identify button
    const identifyButton = screen.getByRole('button', { name: /identify video/i });
    fireEvent.click(identifyButton);
    
    // Check if identifyUrl was called
    await waitFor(() => {
      expect(identifyAPI.identifyUrl).toHaveBeenCalledWith({
        url: 'https://example.com/video.mp4'
      });
      // Check navigation to results page
      expect(mockNavigate).toHaveBeenCalledWith('/results/test-query-123');
    });
  });
  
  test('shows validation error for invalid URL', async () => {
    renderWithContextAndRouter(<VideoIdentifier />);
    
    // Switch to URL tab
    fireEvent.click(screen.getByText(/Video URL/i));
    
    // Enter invalid URL
    const urlInput = screen.getByPlaceholderText(/https:\/\/www\.youtube\.com\/watch\?v=\.\.\./i);
    fireEvent.change(urlInput, {
      target: { value: 'not-a-valid-url' }
    });
    
    // Click identify button
    const identifyButton = screen.getByRole('button', { name: /identify video/i });
    fireEvent.click(identifyButton);
    
    // Check for validation error
    await waitFor(() => {
      expect(screen.getByText(/Please enter a valid video URL from a supported platform/i)).toBeInTheDocument();
    });
  });
});
