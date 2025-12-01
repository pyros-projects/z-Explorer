/**
 * Settings Service Tests
 *
 * Tests for localStorage-based settings persistence.
 * Following TDD approach per implementation plan.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  loadSettings,
  saveSettings,
  validateThumbnailHeight,
  DEFAULT_SETTINGS,
  SETTINGS_KEY
} from '../settingsService';
import type { ZExplorerSettings } from '../settingsService';

describe('settingsService', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  describe('loadSettings', () => {
    it('returns DEFAULT_SETTINGS when localStorage is empty', () => {
      const settings = loadSettings();
      expect(settings).toEqual(DEFAULT_SETTINGS);
    });

    it('merges partial stored data with defaults', () => {
      // Store only gallery settings
      const partial = {
        gallery: {
          layout: 'masonry-vertical',
          thumbnailHeight: 250,
        }
      };
      localStorage.setItem(SETTINGS_KEY, JSON.stringify(partial));

      const settings = loadSettings();

      // Should have merged layout
      expect(settings.gallery.layout).toBe('masonry-vertical');
      expect(settings.gallery.thumbnailHeight).toBe(250);

      // Should have defaults for missing gallery properties
      expect(settings.gallery.thumbnailSize).toBe(DEFAULT_SETTINGS.gallery.thumbnailSize);
      expect(settings.gallery.showPromptOnHover).toBe(DEFAULT_SETTINGS.gallery.showPromptOnHover);

      // Should have defaults for missing sections
      expect(settings.cli).toEqual(DEFAULT_SETTINGS.cli);
      expect(settings.generation).toEqual(DEFAULT_SETTINGS.generation);
      expect(settings.models).toEqual(DEFAULT_SETTINGS.models);
    });

    it('handles corrupted JSON gracefully', () => {
      localStorage.setItem(SETTINGS_KEY, 'not valid json {{{');

      const settings = loadSettings();
      expect(settings).toEqual(DEFAULT_SETTINGS);
    });

    it('handles null values in stored settings', () => {
      const withNulls = {
        gallery: null,
        cli: {
          height: null,
        }
      };
      localStorage.setItem(SETTINGS_KEY, JSON.stringify(withNulls));

      const settings = loadSettings();

      // Should recover gracefully with defaults
      expect(settings.gallery).toBeDefined();
      expect(settings.gallery.layout).toBe(DEFAULT_SETTINGS.gallery.layout);
    });

    it('preserves extra properties from newer settings versions', () => {
      const withExtra = {
        ...DEFAULT_SETTINGS,
        gallery: {
          ...DEFAULT_SETTINGS.gallery,
          futureProperty: 'some value'
        }
      };
      localStorage.setItem(SETTINGS_KEY, JSON.stringify(withExtra));

      const settings = loadSettings() as ZExplorerSettings & { gallery: { futureProperty?: string } };

      // Extra properties should be preserved for forward compatibility
      expect(settings.gallery.futureProperty).toBe('some value');
    });
  });

  describe('saveSettings', () => {
    it('writes to localStorage', () => {
      const settings: ZExplorerSettings = {
        ...DEFAULT_SETTINGS,
        gallery: {
          ...DEFAULT_SETTINGS.gallery,
          layout: 'grid-square'
        }
      };

      const result = saveSettings(settings);

      expect(result).toBe(true);
      const stored = localStorage.getItem(SETTINGS_KEY);
      expect(stored).toBeDefined();

      const parsed = JSON.parse(stored!);
      expect(parsed.gallery.layout).toBe('grid-square');
    });

    it('returns false on storage error', () => {
      // Mock localStorage.setItem to throw
      const originalSetItem = localStorage.setItem;
      localStorage.setItem = vi.fn().mockImplementation(() => {
        throw new Error('QuotaExceededError');
      });

      const result = saveSettings(DEFAULT_SETTINGS);

      expect(result).toBe(false);

      // Restore
      localStorage.setItem = originalSetItem;
    });
  });

  describe('validateThumbnailHeight', () => {
    it('accepts values between 80 and 500', () => {
      expect(validateThumbnailHeight(80)).toBe(true);
      expect(validateThumbnailHeight(200)).toBe(true);
      expect(validateThumbnailHeight(500)).toBe(true);
    });

    it('rejects values below 80', () => {
      expect(validateThumbnailHeight(79)).toBe(false);
      expect(validateThumbnailHeight(0)).toBe(false);
      expect(validateThumbnailHeight(-10)).toBe(false);
    });

    it('rejects values above 500', () => {
      expect(validateThumbnailHeight(501)).toBe(false);
      expect(validateThumbnailHeight(1000)).toBe(false);
    });

    it('rejects non-integer values at boundaries', () => {
      // Edge case: floating point numbers
      expect(validateThumbnailHeight(79.9)).toBe(false);
      expect(validateThumbnailHeight(500.1)).toBe(false);
    });

    it('accepts integer values at exact boundaries', () => {
      expect(validateThumbnailHeight(80)).toBe(true);
      expect(validateThumbnailHeight(500)).toBe(true);
    });
  });

  describe('DEFAULT_SETTINGS', () => {
    it('has all required properties', () => {
      expect(DEFAULT_SETTINGS.gallery).toBeDefined();
      expect(DEFAULT_SETTINGS.cli).toBeDefined();
      expect(DEFAULT_SETTINGS.generation).toBeDefined();
      expect(DEFAULT_SETTINGS.models).toBeDefined();
    });

    it('has sensible default values', () => {
      expect(DEFAULT_SETTINGS.gallery.layout).toBe('flex-row');
      expect(DEFAULT_SETTINGS.gallery.thumbnailSize).toBe('medium');
      expect(DEFAULT_SETTINGS.gallery.thumbnailHeight).toBe(180);
      expect(DEFAULT_SETTINGS.cli.height).toBe(420);
      expect(DEFAULT_SETTINGS.generation.defaultWidth).toBe(1024);
      expect(DEFAULT_SETTINGS.generation.defaultHeight).toBe(1024);
    });
  });
});
