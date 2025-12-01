/**
 * Settings Store
 *
 * Svelte writable store for reactive settings management.
 * Wraps the settingsService for persistence.
 * Per SDD [ref: solution-design.md; lines: 481-544]
 */

import { writable, derived, type Writable, type Readable } from 'svelte/store';
import {
  loadSettings,
  saveSettings,
  getThumbnailHeightPx,
  DEFAULT_SETTINGS,
  type ZExplorerSettings,
  type GallerySettings,
  type CLISettings,
  type GenerationSettings,
  type ModelSettings,
} from '../services/settingsService';

// ============================================================================
// Store Creation
// ============================================================================

/**
 * Internal writable store for settings.
 * Use the exported functions to update.
 */
let _settings: Writable<ZExplorerSettings>;

/**
 * Initialize the settings store.
 * Called automatically on module load, but can be called again for testing.
 */
export function initializeSettings(): void {
  const initial = loadSettings();
  if (_settings) {
    _settings.set(initial);
  } else {
    _settings = writable(initial);
  }
}

// Initialize on module load
initializeSettings();

/**
 * Read-only access to settings.
 * Use update functions to modify.
 */
export const settings: Readable<ZExplorerSettings> = {
  subscribe: (run, invalidate) => _settings.subscribe(run, invalidate),
};

// ============================================================================
// Derived Stores
// ============================================================================

/**
 * Computed thumbnail height in pixels based on current settings.
 * Accounts for preset sizes and custom height.
 */
export const thumbnailHeightPx: Readable<number> = derived(
  settings,
  ($settings) => getThumbnailHeightPx(
    $settings.gallery.thumbnailSize,
    $settings.gallery.thumbnailHeight
  )
);

// ============================================================================
// Update Functions
// ============================================================================

/**
 * Helper to update settings and persist.
 */
function updateAndPersist(updater: (current: ZExplorerSettings) => ZExplorerSettings): void {
  _settings.update((current) => {
    const updated = updater(current);
    saveSettings(updated);
    return updated;
  });
}

/**
 * Update gallery settings.
 * Merges provided changes with existing gallery settings.
 */
export function updateGallery(changes: Partial<GallerySettings>): void {
  updateAndPersist((current) => ({
    ...current,
    gallery: {
      ...current.gallery,
      ...changes,
    },
  }));
}

/**
 * Update CLI settings.
 * Merges provided changes with existing CLI settings.
 */
export function updateCLI(changes: Partial<CLISettings>): void {
  updateAndPersist((current) => ({
    ...current,
    cli: {
      ...current.cli,
      ...changes,
    },
  }));
}

/**
 * Update generation settings.
 * Merges provided changes with existing generation settings.
 */
export function updateGeneration(changes: Partial<GenerationSettings>): void {
  updateAndPersist((current) => ({
    ...current,
    generation: {
      ...current.generation,
      ...changes,
    },
  }));
}

/**
 * Update model settings.
 * Merges provided changes with existing model settings.
 */
export function updateModels(changes: Partial<ModelSettings>): void {
  updateAndPersist((current) => ({
    ...current,
    models: {
      ...current.models,
      ...changes,
    },
  }));
}

/**
 * Reset all settings to defaults.
 */
export function reset(): void {
  _settings.set(DEFAULT_SETTINGS);
  saveSettings(DEFAULT_SETTINGS);
}

// ============================================================================
// Re-export types for convenience
// ============================================================================

export type {
  ZExplorerSettings,
  GallerySettings,
  CLISettings,
  GenerationSettings,
  ModelSettings,
} from '../services/settingsService';

export { DEFAULT_SETTINGS } from '../services/settingsService';
