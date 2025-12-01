/**
 * App Integration Tests
 * Phase 5: Test Settings integration into main App
 *
 * Note: Full App integration tests with mocked fetch are complex due to async loading.
 * These tests focus on individual component behaviors that can be tested reliably.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { get } from 'svelte/store';
import FakeCLI from '../lib/FakeCLI.svelte';
import { settings, updateCLI, reset, initializeSettings } from '../lib/stores/settings';
import { DEFAULT_SETTINGS } from '../lib/services/settingsService';

describe('FakeCLI Settings Command', () => {
  let openSettingsCalled = false;

  beforeEach(() => {
    reset();
    localStorage.clear();
    openSettingsCalled = false;
  });

  it('includes /settings in commands list for autocomplete', async () => {
    render(FakeCLI, {
      props: {
        isGenerating: false,
        isTauriAvailable: false,
        openSettings: () => { openSettingsCalled = true; }
      }
    });

    // Find CLI input
    const input = screen.getByPlaceholderText(/enter prompt/i);

    // Type partial command
    await fireEvent.input(input, { target: { value: '/set' } });

    // Should show /settings in suggestions
    await waitFor(() => {
      expect(screen.getByText('/settings')).toBeInTheDocument();
    });
  });

  it('calls openSettings callback when /settings command is entered', async () => {
    render(FakeCLI, {
      props: {
        isGenerating: false,
        isTauriAvailable: false,
        openSettings: () => { openSettingsCalled = true; }
      }
    });

    // Find CLI input
    const input = screen.getByPlaceholderText(/enter prompt/i);

    // Type /settings command
    await fireEvent.input(input, { target: { value: '/settings' } });
    await fireEvent.keyDown(input, { key: 'Enter' });

    // Callback should be called
    expect(openSettingsCalled).toBe(true);
  });

  it('shows feedback message when opening settings', async () => {
    render(FakeCLI, {
      props: {
        isGenerating: false,
        isTauriAvailable: false,
        openSettings: () => { openSettingsCalled = true; }
      }
    });

    const input = screen.getByPlaceholderText(/enter prompt/i);
    await fireEvent.input(input, { target: { value: '/settings' } });
    await fireEvent.keyDown(input, { key: 'Enter' });

    // Should show feedback
    await waitFor(() => {
      expect(screen.getByText(/Opening settings/i)).toBeInTheDocument();
    });
  });
});

describe('FakeCLI Tips Visibility', () => {
  beforeEach(() => {
    reset();
    localStorage.clear();
  });

  it('shows tips by default when showTipsOnStart is true', async () => {
    render(FakeCLI, {
      props: {
        isGenerating: false,
        isTauriAvailable: false
      }
    });

    // Tips should be visible
    expect(screen.getByText(/Tips:/i)).toBeInTheDocument();
    expect(screen.getByText(/Use __variable__ syntax/i)).toBeInTheDocument();
  });

  it('hides tips when showTipsOnStart setting is false', async () => {
    // Pre-populate localStorage with tips disabled
    const customSettings = {
      ...DEFAULT_SETTINGS,
      cli: { ...DEFAULT_SETTINGS.cli, showTipsOnStart: false }
    };
    localStorage.setItem('z-explorer-settings', JSON.stringify(customSettings));
    initializeSettings();

    render(FakeCLI, {
      props: {
        isGenerating: false,
        isTauriAvailable: false
      }
    });

    // Tips header should still be there but collapsed
    // The detailed tip content should not be visible
    expect(screen.queryByText(/Use __variable__ syntax/i)).not.toBeInTheDocument();
  });

  it('can toggle tips visibility by clicking header', async () => {
    render(FakeCLI, {
      props: {
        isGenerating: false,
        isTauriAvailable: false
      }
    });

    // Tips should be visible initially
    expect(screen.getByText(/Use __variable__ syntax/i)).toBeInTheDocument();

    // Find and click the tips header to collapse
    const tipsHeader = screen.getByTestId('tips-toggle');
    await fireEvent.click(tipsHeader);

    // Tips content should be hidden
    await waitFor(() => {
      expect(screen.queryByText(/Use __variable__ syntax/i)).not.toBeInTheDocument();
    });

    // Click again to expand
    await fireEvent.click(tipsHeader);

    // Tips should be visible again
    await waitFor(() => {
      expect(screen.getByText(/Use __variable__ syntax/i)).toBeInTheDocument();
    });
  });
});

describe('Settings Store Integration', () => {
  beforeEach(() => {
    reset();
    localStorage.clear();
  });

  it('CLI height defaults to 420', () => {
    const currentSettings = get(settings);
    expect(currentSettings.cli.height).toBe(420);
  });

  it('updates CLI height in store', () => {
    updateCLI({ height: 500 });
    const currentSettings = get(settings);
    expect(currentSettings.cli.height).toBe(500);
  });

  it('persists CLI height to localStorage', () => {
    updateCLI({ height: 350 });

    const stored = JSON.parse(localStorage.getItem('z-explorer-settings') || '{}');
    expect(stored.cli.height).toBe(350);
  });

  it('loads CLI height from localStorage on init', () => {
    const customSettings = {
      ...DEFAULT_SETTINGS,
      cli: { ...DEFAULT_SETTINGS.cli, height: 300 }
    };
    localStorage.setItem('z-explorer-settings', JSON.stringify(customSettings));

    initializeSettings();

    const currentSettings = get(settings);
    expect(currentSettings.cli.height).toBe(300);
  });
});
