/**
 * Settings Store Tests
 *
 * Tests for Svelte store wrapping the settings service.
 * Following TDD approach per implementation plan.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { get } from 'svelte/store';
import {
  settings,
  thumbnailHeightPx,
  updateGallery,
  updateCLI,
  updateGeneration,
  updateModels,
  reset,
  initializeSettings
} from '../settings';
import { DEFAULT_SETTINGS, SETTINGS_KEY } from '../../services/settingsService';

describe('settings store', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    // Re-initialize store for each test
    initializeSettings();
  });

  describe('initialization', () => {
    it('initializes from localStorage when empty', () => {
      const current = get(settings);
      expect(current).toEqual(DEFAULT_SETTINGS);
    });

    it('initializes from stored settings', () => {
      // Set up stored settings before initialization
      const stored = {
        ...DEFAULT_SETTINGS,
        gallery: {
          ...DEFAULT_SETTINGS.gallery,
          layout: 'masonry-vertical'
        }
      };
      localStorage.setItem(SETTINGS_KEY, JSON.stringify(stored));

      // Re-initialize
      initializeSettings();

      const current = get(settings);
      expect(current.gallery.layout).toBe('masonry-vertical');
    });
  });

  describe('updateGallery', () => {
    it('merges changes and persists', () => {
      updateGallery({ layout: 'grid-square' });

      const current = get(settings);
      expect(current.gallery.layout).toBe('grid-square');

      // Verify persistence
      const stored = JSON.parse(localStorage.getItem(SETTINGS_KEY)!);
      expect(stored.gallery.layout).toBe('grid-square');
    });

    it('preserves other gallery settings', () => {
      updateGallery({ layout: 'grid-auto' });

      const current = get(settings);
      expect(current.gallery.thumbnailSize).toBe(DEFAULT_SETTINGS.gallery.thumbnailSize);
      expect(current.gallery.showPromptOnHover).toBe(DEFAULT_SETTINGS.gallery.showPromptOnHover);
    });

    it('updates thumbnail size and height together', () => {
      updateGallery({
        thumbnailSize: 'custom',
        thumbnailHeight: 300
      });

      const current = get(settings);
      expect(current.gallery.thumbnailSize).toBe('custom');
      expect(current.gallery.thumbnailHeight).toBe(300);
    });
  });

  describe('updateCLI', () => {
    it('merges changes and persists', () => {
      updateCLI({ height: 500 });

      const current = get(settings);
      expect(current.cli.height).toBe(500);

      // Verify persistence
      const stored = JSON.parse(localStorage.getItem(SETTINGS_KEY)!);
      expect(stored.cli.height).toBe(500);
    });

    it('updates font size', () => {
      updateCLI({ fontSize: 'large' });

      const current = get(settings);
      expect(current.cli.fontSize).toBe('large');
    });
  });

  describe('updateGeneration', () => {
    it('merges changes and persists', () => {
      updateGeneration({ defaultWidth: 512, defaultHeight: 768 });

      const current = get(settings);
      expect(current.generation.defaultWidth).toBe(512);
      expect(current.generation.defaultHeight).toBe(768);
    });

    it('updates auto-enhance setting', () => {
      updateGeneration({ autoEnhance: true });

      const current = get(settings);
      expect(current.generation.autoEnhance).toBe(true);
    });
  });

  describe('updateModels', () => {
    it('merges changes and persists', () => {
      updateModels({
        imageMode: 'hf_local',
        imagePath: '/custom/path'
      });

      const current = get(settings);
      expect(current.models.imageMode).toBe('hf_local');
      expect(current.models.imagePath).toBe('/custom/path');
    });

    it('can clear model overrides', () => {
      // First set some values
      updateModels({ imageMode: 'sdnq' });
      expect(get(settings).models.imageMode).toBe('sdnq');

      // Then clear them
      updateModels({ imageMode: null });
      expect(get(settings).models.imageMode).toBeNull();
    });
  });

  describe('reset', () => {
    it('restores defaults and persists', () => {
      // Make some changes
      updateGallery({ layout: 'grid-square', thumbnailHeight: 400 });
      updateCLI({ fontSize: 'large' });

      // Verify changes took effect
      expect(get(settings).gallery.layout).toBe('grid-square');
      expect(get(settings).cli.fontSize).toBe('large');

      // Reset
      reset();

      const current = get(settings);
      expect(current).toEqual(DEFAULT_SETTINGS);

      // Verify persistence
      const stored = JSON.parse(localStorage.getItem(SETTINGS_KEY)!);
      expect(stored).toEqual(DEFAULT_SETTINGS);
    });
  });

  describe('thumbnailHeightPx derived store', () => {
    it('computes correctly for preset sizes', () => {
      updateGallery({ thumbnailSize: 'small' });
      expect(get(thumbnailHeightPx)).toBe(120);

      updateGallery({ thumbnailSize: 'medium' });
      expect(get(thumbnailHeightPx)).toBe(180);

      updateGallery({ thumbnailSize: 'large' });
      expect(get(thumbnailHeightPx)).toBe(250);

      updateGallery({ thumbnailSize: 'xlarge' });
      expect(get(thumbnailHeightPx)).toBe(350);
    });

    it('uses custom height when thumbnailSize is custom', () => {
      updateGallery({ thumbnailSize: 'custom', thumbnailHeight: 275 });
      expect(get(thumbnailHeightPx)).toBe(275);
    });

    it('falls back to default for invalid custom height', () => {
      updateGallery({ thumbnailSize: 'custom', thumbnailHeight: 50 }); // Below minimum
      expect(get(thumbnailHeightPx)).toBe(180); // Default fallback
    });

    it('updates reactively when settings change', () => {
      const values: number[] = [];

      const unsubscribe = thumbnailHeightPx.subscribe((value) => {
        values.push(value);
      });

      updateGallery({ thumbnailSize: 'large' });
      updateGallery({ thumbnailSize: 'small' });

      // Should have recorded initial + 2 updates
      expect(values.length).toBe(3);
      expect(values).toContain(250); // large
      expect(values).toContain(120); // small

      unsubscribe();
    });
  });
});
