/**
 * Sample test for Dashboard component
 */

import { describe, it, expect } from 'vitest';
import { renderWithProviders, screen } from '@/test/utils';
import { Dashboard } from '@/components/Dashboard/Dashboard';

describe('Dashboard', () => {
  it('renders dashboard with tabs', () => {
    renderWithProviders(<Dashboard />);
    
    // Check if overview tab is visible
    expect(screen.getByText(/overview/i)).toBeInTheDocument();
  });

  it('renders workflow tab', () => {
    renderWithProviders(<Dashboard />);
    
    // Check if workflows tab exists
    expect(screen.getByText(/workflows/i)).toBeInTheDocument();
  });
});

