/**
 * Settings Service
 *
 * Manages user preferences via localStorage with validation and persistence.
 * Per SDD [ref: solution-design.md; lines: 481-544]
 */

// ============================================================================
// Type Definitions
// ============================================================================

export type GalleryLayout =
  | 'flex-row'
  | 'masonry-vertical'
  | 'masonry-horizontal'
  | 'grid-square'
  | 'grid-auto';

export type ThumbnailSize = 'small' | 'medium' | 'large' | 'xlarge' | 'custom';

export type SortOrder = 'newest' | 'oldest';

export type FontSize = 'small' | 'medium' | 'large';

export interface GallerySettings {
  layout: GalleryLayout;
  thumbnailSize: ThumbnailSize;
  thumbnailHeight: number;
  showPromptOnHover: boolean;
  sortOrder: SortOrder;
}

export interface CLISettings {
  height: number;
  showTipsOnStart: boolean;
  showTutorialOnStart: boolean;
  fontSize: FontSize;
  showHistory: boolean;
}

export interface GenerationSettings {
  defaultWidth: number;
  defaultHeight: number;
  defaultCount: number;
  autoEnhance: boolean;
}

export interface ModelSettings {
  imageMode: string | null;
  imageRepo: string | null;
  imagePath: string | null;
  llmMode: string | null;
  llmRepo: string | null;
  llmPath: string | null;
}

export interface ZExplorerSettings {
  gallery: GallerySettings;
  cli: CLISettings;
  generation: GenerationSettings;
  models: ModelSettings;
}

// ============================================================================
// Constants
// ============================================================================

export const SETTINGS_KEY = 'z-explorer-settings';

export const DEFAULT_SETTINGS: ZExplorerSettings = {
  gallery: {
    layout: 'flex-row',
    thumbnailSize: 'medium',
    thumbnailHeight: 180,
    showPromptOnHover: true,
    sortOrder: 'newest',
  },
  cli: {
    height: 420,
    showTipsOnStart: true,
    showTutorialOnStart: true,
    fontSize: 'medium',
    showHistory: true,
  },
  generation: {
    defaultWidth: 1024,
    defaultHeight: 1024,
    defaultCount: 1,
    autoEnhance: false,
  },
  models: {
    imageMode: null,
    imageRepo: null,
    imagePath: null,
    llmMode: null,
    llmRepo: null,
    llmPath: null,
  },
};

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Deep merge two objects, with source values taking precedence.
 * Handles nested objects recursively.
 * Uses explicit ZExplorerSettings type for proper type inference.
 */
function deepMergeSettings(
  target: ZExplorerSettings,
  source: unknown
): ZExplorerSettings {
  if (!source || typeof source !== 'object') {
    return target;
  }

  const src = source as Record<string, unknown>;
  const result = { ...target };

  // Merge gallery settings
  if (src.gallery && typeof src.gallery === 'object') {
    result.gallery = {
      ...target.gallery,
      ...(src.gallery as Partial<GallerySettings>),
    };
  }

  // Merge CLI settings
  if (src.cli && typeof src.cli === 'object') {
    result.cli = {
      ...target.cli,
      ...(src.cli as Partial<CLISettings>),
    };
  }

  // Merge generation settings
  if (src.generation && typeof src.generation === 'object') {
    result.generation = {
      ...target.generation,
      ...(src.generation as Partial<GenerationSettings>),
    };
  }

  // Merge model settings
  if (src.models && typeof src.models === 'object') {
    result.models = {
      ...target.models,
      ...(src.models as Partial<ModelSettings>),
    };
  }

  return result;
}

// ============================================================================
// Public API
// ============================================================================

/**
 * Load settings from localStorage, merging with defaults.
 * Returns DEFAULT_SETTINGS if nothing stored or on error.
 */
export function loadSettings(): ZExplorerSettings {
  try {
    const stored = localStorage.getItem(SETTINGS_KEY);
    if (!stored) {
      return DEFAULT_SETTINGS;
    }

    const parsed = JSON.parse(stored);

    // Deep merge with defaults to handle missing fields from older versions
    return deepMergeSettings(DEFAULT_SETTINGS, parsed);
  } catch (e) {
    console.warn('Failed to load settings, using defaults:', e);
    return DEFAULT_SETTINGS;
  }
}

/**
 * Save settings to localStorage.
 * Returns true on success, false on error.
 */
export function saveSettings(settings: ZExplorerSettings): boolean {
  try {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
    return true;
  } catch (e) {
    console.error('Failed to save settings:', e);
    return false;
  }
}

/**
 * Validate thumbnail height is within allowed range (80-500px).
 * Per PRD Feature 3 acceptance criteria.
 */
export function validateThumbnailHeight(height: number): boolean {
  return typeof height === 'number' && isFinite(height) && height >= 80 && height <= 500;
}

/**
 * Get pixel value for thumbnail size preset.
 */
export function getThumbnailHeightPx(
  size: ThumbnailSize,
  customHeight: number
): number {
  switch (size) {
    case 'small':
      return 120;
    case 'medium':
      return 180;
    case 'large':
      return 250;
    case 'xlarge':
      return 350;
    case 'custom':
      return validateThumbnailHeight(customHeight) ? customHeight : 180;
    default:
      return 180;
  }
}
