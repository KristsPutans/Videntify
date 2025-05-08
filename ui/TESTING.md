# Videntify UI Testing Guide

## Overview

This document outlines the testing strategy for the Videntify UI. We use a comprehensive testing approach including unit tests, integration tests, and end-to-end tests to ensure that all components of the application work correctly together.

## Test Organization

Tests are organized into the following categories:

- **Unit Tests**: Located alongside the components they test (`__tests__` directories)
- **Integration Tests**: Located in `src/tests/integration`
- **Mock Data and Utilities**: Located in `src/utils/testUtils.js` and `src/utils/integrationTestUtils.js`

## Testing Technologies

- **Jest**: Testing framework
- **React Testing Library**: For testing React components
- **Jest Mock Axios**: For mocking API calls
- **MSW (Mock Service Worker)**: For advanced API mocking (if needed in the future)

## CI/CD Integration

### GitHub Actions Workflow

The project includes a CI/CD pipeline implemented with GitHub Actions. The workflow is defined in `.github/workflows/ci.yml` and includes the following jobs:

1. **test-ui**: Runs UI tests using Jest
2. **test-backend**: Runs backend tests using pytest
3. **build-ui**: Builds the UI for deployment
4. **deploy-ui-production**: Deploys to production environment (main branch)
5. **deploy-ui-staging**: Deploys to staging environment (develop branch)

### Test Configuration for CI

Some tests that rely on browser-specific features or complex interactions are marked to be skipped in the CI environment using the `test:ci` script in package.json.

### Adding Tests Safe for CI

When writing new tests, consider the following guidelines to ensure they run properly in the CI environment:

- Avoid tests that depend on window-specific behavior
- Mock all external API calls
- Don't rely on specific timing that might be affected by CI performance
- Use the `data-testid` attributes for selecting elements rather than text content when appropriate

## Running Tests

### All Tests

To run all tests once (CI mode):

```bash
npm run test:ci
```

This command is specifically designed for our CI/CD environment and skips tests that might be problematic in automated environments.

### With Coverage Report

To run all tests with coverage report:

```bash
npm run test:coverage
```

### Watch Mode (Development)

To run tests in watch mode during development:

```bash
npm test
```

### Running Specific Tests

To run specific tests, you can provide a pattern:

```bash
npm test -- -t "Login Component"
```

## Writing Tests

### Unit Tests

Unit tests should focus on testing a single component in isolation. Mock all dependencies.

Example:

```jsx
import { render, screen } from '@testing-library/react';
import UserProfileDropdown from '../UserProfileDropdown';

test('renders user name correctly', () => {
  render(<UserProfileDropdown user={{ name: 'Test User' }} />);
  expect(screen.getByText('Test User')).toBeInTheDocument();
});
```

### Integration Tests

Integration tests should focus on testing how components work together.

Example:

```jsx
import { render, screen } from '@testing-library/react';
import { renderWithProviders } from '../../utils/integrationTestUtils';
import App from '../../App';

test('navigation flow between components', async () => {
  renderWithProviders(<App />);
  // Test user flow between multiple components
});
```

## Mocking

### API Mocks

Use the `testUtils.js` file for common mock data and API responses.

Example:

```jsx
import { mockApiResponses } from '../../utils/testUtils';

// Mock API call
jest.mock('../../services/api', () => ({
  authAPI: {
    login: jest.fn().mockResolvedValue(mockApiResponses['/auth/login'])
  }
}));
```

## CI/CD Integration

Tests are automatically run as part of our CI/CD pipeline. See the GitHub Actions workflow in `.github/workflows/ci.yml`.

## Coverage Goals

- Unit tests: Aim for 80%+ coverage
- Integration tests: Focus on critical user flows
- End-to-end tests: Cover main user journeys

## Troubleshooting Common Test Issues

### Tests Failing in CI but Passing Locally

- Check for environment-specific code
- Ensure all required environment variables are set in CI
- Verify test timeouts are sufficient for CI environment

### Handling Asynchronous Tests

Always use `async/await` with proper waitFor conditions:

```jsx
test('async operation completes', async () => {
  // Setup
  
  // Action
  userEvent.click(button);
  
  // Wait for condition
  await waitFor(() => {
    expect(something).toBeVisible();
  });
});
```
