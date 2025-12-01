<script lang="ts">
  import { onMount } from 'svelte';
  import {
    settings,
    updateGallery,
    updateCLI,
    updateGeneration,
    reset,
  } from './stores/settings';
  import {
    type GalleryLayout,
    type ThumbnailSize,
    type ZExplorerSettings,
    validateThumbnailHeight,
    DEFAULT_SETTINGS,
  } from './services/settingsService';

  export let open = false;
  export let onClose: () => void;

  // Tabs
  type Tab = 'gallery' | 'cli' | 'generation' | 'models';
  let activeTab: Tab = 'gallery';

  // Local state (copy of settings for editing)
  let localSettings: ZExplorerSettings = structuredClone(DEFAULT_SETTINGS);

  // Validation
  let thumbnailError = '';
  let showResetConfirm = false;

  // Layout options with labels and icons
  const layoutOptions: { value: GalleryLayout; label: string; icon: string }[] = [
    { value: 'flex-row', label: 'Flex Row', icon: '═' },
    { value: 'masonry-vertical', label: 'Masonry Vertical', icon: '▓' },
    { value: 'masonry-horizontal', label: 'Masonry Horizontal', icon: '▒' },
    { value: 'grid-square', label: 'Grid Square', icon: '▦' },
    { value: 'grid-auto', label: 'Grid Auto', icon: '▤' },
  ];

  // Thumbnail size presets
  const thumbnailPresets: { value: ThumbnailSize; label: string; height: number }[] = [
    { value: 'small', label: 'Small', height: 120 },
    { value: 'medium', label: 'Medium', height: 180 },
    { value: 'large', label: 'Large', height: 250 },
    { value: 'xlarge', label: 'X-Large', height: 350 },
    { value: 'custom', label: 'Custom', height: 0 },
  ];

  // Font size options
  const fontSizeOptions: { value: 'small' | 'medium' | 'large'; label: string }[] = [
    { value: 'small', label: 'Small' },
    { value: 'medium', label: 'Medium' },
    { value: 'large', label: 'Large' },
  ];

  // CLI panel height options
  const cliHeightOptions: { value: number; label: string }[] = [
    { value: 250, label: 'Compact (250px)' },
    { value: 350, label: 'Small (350px)' },
    { value: 420, label: 'Medium (420px)' },
    { value: 500, label: 'Large (500px)' },
    { value: 600, label: 'Maximum (600px)' },
  ];

  // Model mode options
  const imageModeOptions: { value: string; label: string }[] = [
    { value: 'hf_download', label: 'HuggingFace Download' },
    { value: 'hf_local', label: 'Local HF Clone' },
    { value: 'sdnq', label: 'SDNQ Quantized' },
    { value: 'components', label: 'Components' },
  ];

  const llmModeOptions: { value: string; label: string }[] = [
    { value: 'hf_download', label: 'HuggingFace Download' },
    { value: 'hf_local', label: 'Local HF Clone' },
    { value: 'gguf', label: 'GGUF File' },
    { value: 'z_image', label: 'Z-Image Encoder' },
  ];

  // Model settings local state
  let imageMode = 'hf_download';
  let imageRepo = '';
  let imagePath = '';
  let llmMode = 'hf_download';
  let llmRepo = '';
  let llmPath = '';

  // Model action states
  let testingConnection = false;
  let testResult: { valid: boolean; message: string } | null = null;
  let reloadingModels = false;
  let reloadResult: { status: string; message?: string } | null = null;

  // Initialize local settings when dialog opens
  $: if (open) {
    localSettings = structuredClone($settings);
    activeTab = 'gallery';
    thumbnailError = '';
    showResetConfirm = false;
    // Reset model states
    testResult = null;
    reloadResult = null;
    // Initialize from settings store
    imageMode = localSettings.models.imageMode || 'hf_download';
    imageRepo = localSettings.models.imageRepo || '';
    imagePath = localSettings.models.imagePath || '';
    llmMode = localSettings.models.llmMode || 'hf_download';
    llmRepo = localSettings.models.llmRepo || '';
    llmPath = localSettings.models.llmPath || '';
  }

  // Validate thumbnail height
  function validateCustomHeight(height: number) {
    if (!validateThumbnailHeight(height)) {
      thumbnailError = 'Must be between 80 and 500 pixels';
    } else {
      thumbnailError = '';
    }
  }

  // Handle thumbnail size preset selection
  function selectThumbnailPreset(preset: ThumbnailSize) {
    const presetData = thumbnailPresets.find(p => p.value === preset);
    const height = preset !== 'custom' && presetData ? presetData.height : localSettings.gallery.thumbnailHeight;
    if (preset !== 'custom') {
      thumbnailError = '';
    }
    localSettings = {
      ...localSettings,
      gallery: {
        ...localSettings.gallery,
        thumbnailSize: preset,
        thumbnailHeight: height
      }
    };
  }

  // Handle custom thumbnail height input
  function handleCustomHeightInput(event: Event) {
    const input = event.target as HTMLInputElement;
    const value = parseInt(input.value, 10);
    validateCustomHeight(value);
    localSettings = {
      ...localSettings,
      gallery: { ...localSettings.gallery, thumbnailHeight: value }
    };
  }

  // Handle layout selection
  function selectLayout(layout: GalleryLayout) {
    localSettings = {
      ...localSettings,
      gallery: { ...localSettings.gallery, layout }
    };
  }

  // Check if there are validation errors
  $: hasErrors = thumbnailError !== '';

  // Handle Save
  function handleSave() {
    if (hasErrors) return;

    // Commit changes to store
    updateGallery(localSettings.gallery);
    updateCLI(localSettings.cli);
    updateGeneration(localSettings.generation);

    onClose();
  }

  // Handle Cancel
  function handleCancel() {
    onClose();
  }

  // Handle Reset
  function handleResetClick() {
    showResetConfirm = true;
  }

  function confirmReset() {
    reset();
    localSettings = structuredClone(DEFAULT_SETTINGS);
    showResetConfirm = false;
    thumbnailError = '';
  }

  function cancelReset() {
    showResetConfirm = false;
  }

  // Handle keyboard
  function handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Escape') {
      if (showResetConfirm) {
        cancelReset();
      } else {
        onClose();
      }
    }
  }

  // Handle overlay click
  function handleOverlayClick(event: MouseEvent) {
    if (event.target === event.currentTarget) {
      onClose();
    }
  }

  // Model API functions
  async function testConnection() {
    testingConnection = true;
    testResult = null;
    reloadResult = null;

    try {
      // Test image model config
      const imageResponse = await fetch('/api/settings/models/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model_type: 'image',
          mode: imageMode,
          repo: imageRepo || null,
          path: imagePath || null,
        }),
      });

      const imageResult = await imageResponse.json();
      if (!imageResult.valid) {
        testResult = { valid: false, message: `Image: ${imageResult.message}` };
        return;
      }

      // Test LLM config
      const llmResponse = await fetch('/api/settings/models/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model_type: 'llm',
          mode: llmMode,
          repo: llmRepo || null,
          path: llmPath || null,
        }),
      });

      const llmResult = await llmResponse.json();
      if (!llmResult.valid) {
        testResult = { valid: false, message: `LLM: ${llmResult.message}` };
        return;
      }

      testResult = { valid: true, message: 'Configuration valid!' };
    } catch (error) {
      testResult = { valid: false, message: `Connection error: ${error}` };
    } finally {
      testingConnection = false;
    }
  }

  async function reloadModels() {
    reloadingModels = true;
    reloadResult = null;

    try {
      // First update the settings
      const updateResponse = await fetch('/api/settings/models', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          image_mode: imageMode,
          image_repo: imageRepo || null,
          image_path: imagePath || null,
          llm_mode: llmMode,
          llm_repo: llmRepo || null,
          llm_path: llmPath || null,
        }),
      });

      const updateResult = await updateResponse.json();
      if (updateResult.status !== 'ok') {
        reloadResult = { status: 'error', message: updateResult.message };
        return;
      }

      // Then reload models
      const reloadResponse = await fetch('/api/models/reload', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });

      const result = await reloadResponse.json();
      reloadResult = result;

      if (result.status === 'ok') {
        // Update local settings store with new model config
        localSettings.models = {
          imageMode,
          imageRepo,
          imagePath,
          llmMode,
          llmRepo,
          llmPath,
        };
      }
    } catch (error) {
      reloadResult = { status: 'error', message: `Error: ${error}` };
    } finally {
      reloadingModels = false;
    }
  }

  // Helper to determine if repo or path input should show
  function needsRepoInput(mode: string): boolean {
    return mode === 'hf_download' || mode === 'sdnq';
  }

  function needsPathInput(mode: string): boolean {
    return mode === 'hf_local' || mode === 'components' || mode === 'gguf';
  }
</script>

{#if open}
  <!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
  <div
    class="settings-overlay"
    role="dialog"
    aria-modal="true"
    aria-labelledby="settings-title"
    data-testid="settings-overlay"
    on:click={handleOverlayClick}
    on:keydown={handleKeydown}
  >
    <!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
    <div class="settings-dialog" data-testid="settings-content" on:click|stopPropagation>
      <!-- Header -->
      <div class="settings-header">
        <h2 id="settings-title">Settings</h2>
        <button class="close-btn" on:click={onClose} aria-label="Close settings">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 6L6 18M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Tabs -->
      <div class="tabs" role="tablist">
        <button
          role="tab"
          aria-selected={activeTab === 'gallery'}
          class:active={activeTab === 'gallery'}
          on:click={() => (activeTab = 'gallery')}
        >
          Gallery
        </button>
        <button
          role="tab"
          aria-selected={activeTab === 'cli'}
          class:active={activeTab === 'cli'}
          on:click={() => (activeTab = 'cli')}
        >
          CLI
        </button>
        <button
          role="tab"
          aria-selected={activeTab === 'generation'}
          class:active={activeTab === 'generation'}
          on:click={() => (activeTab = 'generation')}
        >
          Generation
        </button>
        <button
          role="tab"
          aria-selected={activeTab === 'models'}
          class:active={activeTab === 'models'}
          on:click={() => (activeTab = 'models')}
        >
          Models
        </button>
      </div>

      <!-- Tab Content -->
      <div class="tab-content">
        {#if activeTab === 'gallery'}
          <div class="tab-panel" role="tabpanel">
            <!-- Layout Selection -->
            <div class="setting-group">
              <h3>Gallery Layout</h3>
              <div class="layout-options">
                {#each layoutOptions as opt}
                  <button
                    class="layout-option"
                    class:selected={localSettings.gallery.layout === opt.value}
                    data-testid="layout-{opt.value}"
                    on:click={() => selectLayout(opt.value)}
                  >
                    <span class="layout-icon">{opt.icon}</span>
                    <span class="layout-label">{opt.label}</span>
                  </button>
                {/each}
              </div>
            </div>

            <!-- Thumbnail Size -->
            <div class="setting-group">
              <h3>Thumbnail Size</h3>
              <div class="radio-group">
                {#each thumbnailPresets as preset}
                  <label class="radio-label">
                    <input
                      type="radio"
                      name="thumbnailSize"
                      value={preset.value}
                      checked={localSettings.gallery.thumbnailSize === preset.value}
                      on:change={() => selectThumbnailPreset(preset.value)}
                    />
                    <span class="radio-text">{preset.label}</span>
                    {#if preset.value !== 'custom'}
                      <span class="radio-hint">{preset.height}px</span>
                    {/if}
                  </label>
                {/each}
              </div>

              {#if localSettings.gallery.thumbnailSize === 'custom'}
                <div class="custom-input-group">
                  <label for="custom-thumbnail">Custom Height (px)</label>
                  <input
                    id="custom-thumbnail"
                    type="number"
                    min="80"
                    max="500"
                    value={localSettings.gallery.thumbnailHeight}
                    data-testid="custom-thumbnail-input"
                    on:input={handleCustomHeightInput}
                  />
                  {#if thumbnailError}
                    <span class="error-text">{thumbnailError}</span>
                  {/if}
                </div>
              {/if}
            </div>

            <!-- Show Prompt on Hover -->
            <div class="setting-group">
              <label class="checkbox-label">
                <input
                  type="checkbox"
                  bind:checked={localSettings.gallery.showPromptOnHover}
                />
                <span>Show prompt on hover</span>
              </label>
            </div>

            <!-- Sort Order -->
            <div class="setting-group">
              <h3>Sort Order</h3>
              <select bind:value={localSettings.gallery.sortOrder}>
                <option value="newest">Newest First</option>
                <option value="oldest">Oldest First</option>
                <option value="name">By Name</option>
              </select>
            </div>
          </div>
        {:else if activeTab === 'cli'}
          <div class="tab-panel" role="tabpanel">
            <!-- CLI Panel Height -->
            <div class="setting-group">
              <h3>Panel Height</h3>
              <div class="radio-group">
                {#each cliHeightOptions as opt}
                  <label class="radio-label">
                    <input
                      type="radio"
                      name="cliHeight"
                      value={opt.value}
                      checked={localSettings.cli.height === opt.value}
                      on:change={() => { localSettings.cli.height = opt.value; }}
                    />
                    <span class="radio-text">{opt.label}</span>
                  </label>
                {/each}
              </div>
            </div>

            <!-- Font Size -->
            <div class="setting-group">
              <h3>Font Size</h3>
              <div class="radio-group">
                {#each fontSizeOptions as opt}
                  <label class="radio-label">
                    <input
                      type="radio"
                      name="fontSize"
                      value={opt.value}
                      checked={localSettings.cli.fontSize === opt.value}
                      on:change={() => { localSettings.cli.fontSize = opt.value; }}
                    />
                    <span class="radio-text">{opt.label}</span>
                  </label>
                {/each}
              </div>
            </div>

            <!-- Show Tips on Startup -->
            <div class="setting-group">
              <label class="checkbox-label">
                <input
                  type="checkbox"
                  bind:checked={localSettings.cli.showTipsOnStart}
                />
                <span>Show tips on startup</span>
              </label>
            </div>

            <!-- Show Tutorial on Startup -->
            <div class="setting-group">
              <label class="checkbox-label">
                <input
                  type="checkbox"
                  bind:checked={localSettings.cli.showTutorialOnStart}
                />
                <span>Show tutorial on startup</span>
              </label>
            </div>
          </div>
        {:else if activeTab === 'generation'}
          <div class="tab-panel" role="tabpanel">
            <!-- Default Dimensions -->
            <div class="setting-group">
              <h3>Default Dimensions</h3>
              <div class="dimension-inputs">
                <div class="input-group">
                  <label for="default-width">Default Width</label>
                  <input
                    id="default-width"
                    type="number"
                    min="256"
                    max="2048"
                    step="64"
                    bind:value={localSettings.generation.defaultWidth}
                  />
                </div>
                <span class="dimension-separator">×</span>
                <div class="input-group">
                  <label for="default-height">Default Height</label>
                  <input
                    id="default-height"
                    type="number"
                    min="256"
                    max="2048"
                    step="64"
                    bind:value={localSettings.generation.defaultHeight}
                  />
                </div>
              </div>
            </div>

            <!-- Default Count -->
            <div class="setting-group">
              <div class="input-group">
                <label for="default-count">Default Count</label>
                <input
                  id="default-count"
                  type="number"
                  min="1"
                  max="10"
                  bind:value={localSettings.generation.defaultCount}
                />
              </div>
            </div>

            <!-- Auto-enhance -->
            <div class="setting-group">
              <label class="checkbox-label">
                <input
                  type="checkbox"
                  bind:checked={localSettings.generation.autoEnhance}
                />
                <span>Auto-enhance prompts with LLM</span>
              </label>
            </div>
          </div>
        {:else if activeTab === 'models'}
          <div class="tab-panel" role="tabpanel">
            <!-- Image Model Section -->
            <div class="setting-group">
              <h3>Image Model</h3>
              <div class="model-config">
                <div class="input-row">
                  <label for="image-mode">Mode</label>
                  <select
                    id="image-mode"
                    data-testid="image-mode-select"
                    bind:value={imageMode}
                  >
                    {#each imageModeOptions as opt}
                      <option value={opt.value}>{opt.label}</option>
                    {/each}
                  </select>
                </div>

                {#if needsRepoInput(imageMode)}
                  <div class="input-row">
                    <label for="image-repo">Repository</label>
                    <input
                      id="image-repo"
                      type="text"
                      data-testid="image-repo-input"
                      placeholder="e.g., Tongyi-MAI/Z-Image-Turbo"
                      bind:value={imageRepo}
                    />
                  </div>
                {/if}

                {#if needsPathInput(imageMode)}
                  <div class="input-row">
                    <label for="image-path">Local Path</label>
                    <input
                      id="image-path"
                      type="text"
                      data-testid="image-path-input"
                      placeholder="/path/to/model"
                      bind:value={imagePath}
                    />
                  </div>
                {/if}
              </div>
            </div>

            <!-- LLM Model Section -->
            <div class="setting-group">
              <h3>LLM Model</h3>
              <div class="model-config">
                <div class="input-row">
                  <label for="llm-mode">Mode</label>
                  <select
                    id="llm-mode"
                    data-testid="llm-mode-select"
                    bind:value={llmMode}
                  >
                    {#each llmModeOptions as opt}
                      <option value={opt.value}>{opt.label}</option>
                    {/each}
                  </select>
                </div>

                {#if needsRepoInput(llmMode)}
                  <div class="input-row">
                    <label for="llm-repo">Repository</label>
                    <input
                      id="llm-repo"
                      type="text"
                      data-testid="llm-repo-input"
                      placeholder="e.g., unsloth/Qwen3-4B-Instruct-2507-bnb-4bit"
                      bind:value={llmRepo}
                    />
                  </div>
                {/if}

                {#if needsPathInput(llmMode)}
                  <div class="input-row">
                    <label for="llm-path">Local Path</label>
                    <input
                      id="llm-path"
                      type="text"
                      data-testid="llm-path-input"
                      placeholder="/path/to/llm"
                      bind:value={llmPath}
                    />
                  </div>
                {/if}
              </div>
            </div>

            <!-- Model Actions -->
            <div class="setting-group model-actions">
              <div class="action-buttons">
                <button
                  class="btn btn-secondary"
                  on:click={testConnection}
                  disabled={testingConnection}
                >
                  {testingConnection ? 'Testing...' : 'Test Connection'}
                </button>
                <button
                  class="btn btn-primary"
                  on:click={reloadModels}
                  disabled={reloadingModels || !testResult?.valid}
                >
                  {reloadingModels ? 'Reloading...' : 'Reload Models'}
                </button>
              </div>

              {#if testResult}
                <div class="result-message" class:success={testResult.valid} class:error={!testResult.valid}>
                  {testResult.valid ? '✓' : '✗'} {testResult.message}
                </div>
              {/if}

              {#if reloadResult}
                <div class="result-message" class:success={reloadResult.status === 'ok'} class:error={reloadResult.status !== 'ok'}>
                  {reloadResult.status === 'ok' ? '✓ Models reloaded!' : `✗ ${reloadResult.message}`}
                  {#if reloadResult.status === 'ok' && reloadResult.duration_ms}
                    <span class="duration">({reloadResult.duration_ms}ms)</span>
                  {/if}
                </div>
              {/if}

              <p class="model-hint">
                💡 Changes override your .env configuration for this session only.
                They are stored in localStorage and do NOT modify your .env file.
              </p>
            </div>
          </div>
        {/if}
      </div>

      <!-- Footer -->
      <div class="settings-footer">
        <button class="btn btn-secondary" on:click={handleResetClick}>
          Reset to Defaults
        </button>
        <div class="footer-right">
          <button class="btn btn-ghost" on:click={handleCancel}>
            Cancel
          </button>
          <button class="btn btn-primary" on:click={handleSave} disabled={hasErrors}>
            Save
          </button>
        </div>
      </div>

      <!-- Reset Confirmation Modal -->
      {#if showResetConfirm}
        <div class="confirm-overlay">
          <div class="confirm-dialog">
            <h3>Reset Settings?</h3>
            <p>Are you sure you want to reset all settings to their default values? This cannot be undone.</p>
            <div class="confirm-actions">
              <button class="btn btn-ghost" on:click={cancelReset}>Cancel</button>
              <button class="btn btn-danger" on:click={confirmReset}>Confirm</button>
            </div>
          </div>
        </div>
      {/if}
    </div>
  </div>
{/if}

<style>
  .settings-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.8);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    animation: fadeIn 0.2s ease-out;
  }

  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  .settings-dialog {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    width: 90%;
    max-width: 600px;
    max-height: 85vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5),
                0 0 40px rgba(139, 92, 246, 0.15);
    animation: slideIn 0.2s ease-out;
  }

  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateY(-20px) scale(0.95);
    }
    to {
      opacity: 1;
      transform: translateY(0) scale(1);
    }
  }

  .settings-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20px 24px;
    border-bottom: 1px solid var(--border-color);
  }

  .settings-header h2 {
    font-size: 20px;
    font-weight: 600;
    background: var(--gradient-brand);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .close-btn {
    background: transparent;
    border: none;
    color: var(--text-muted);
    cursor: pointer;
    padding: 8px;
    border-radius: 8px;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .close-btn:hover {
    background: var(--bg-tertiary);
    color: var(--text-primary);
  }

  /* Tabs */
  .tabs {
    display: flex;
    padding: 0 24px;
    border-bottom: 1px solid var(--border-color);
    gap: 4px;
  }

  .tabs button {
    background: transparent;
    border: none;
    color: var(--text-muted);
    padding: 12px 16px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    position: relative;
    transition: all 0.2s;
  }

  .tabs button:hover {
    color: var(--text-secondary);
  }

  .tabs button.active {
    color: var(--accent-primary);
  }

  .tabs button.active::after {
    content: '';
    position: absolute;
    bottom: -1px;
    left: 0;
    right: 0;
    height: 2px;
    background: var(--gradient-brand);
    border-radius: 2px 2px 0 0;
  }

  /* Tab Content */
  .tab-content {
    flex: 1;
    overflow-y: auto;
    padding: 24px;
  }

  .tab-panel {
    display: flex;
    flex-direction: column;
    gap: 24px;
  }

  .setting-group {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .setting-group h3 {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  /* Layout Options */
  .layout-options {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
    gap: 8px;
  }

  .layout-option {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    padding: 16px 12px;
    background: var(--bg-tertiary);
    border: 2px solid transparent;
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .layout-option:hover {
    border-color: var(--border-color);
    background: var(--bg-card);
  }

  .layout-option.selected {
    border-color: var(--accent-primary);
    background: rgba(139, 92, 246, 0.1);
  }

  .layout-icon {
    font-size: 24px;
    opacity: 0.7;
  }

  .layout-option.selected .layout-icon {
    opacity: 1;
  }

  .layout-label {
    font-size: 12px;
    color: var(--text-secondary);
    text-align: center;
  }

  .layout-option.selected .layout-label {
    color: var(--accent-primary);
  }

  /* Radio Group */
  .radio-group {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .radio-label {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 16px;
    background: var(--bg-tertiary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .radio-label:hover {
    border-color: var(--accent-primary);
  }

  .radio-label:has(input:checked) {
    background: rgba(139, 92, 246, 0.1);
    border-color: var(--accent-primary);
  }

  .radio-label input {
    accent-color: var(--accent-primary);
  }

  .radio-text {
    font-size: 14px;
    color: var(--text-primary);
  }

  .radio-hint {
    font-size: 12px;
    color: var(--text-muted);
  }

  /* Custom Input */
  .custom-input-group {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-top: 8px;
  }

  .custom-input-group label {
    font-size: 13px;
    color: var(--text-secondary);
  }

  .custom-input-group input {
    width: 120px;
    padding: 10px 12px;
    background: var(--bg-tertiary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    color: var(--text-primary);
    font-size: 14px;
  }

  .custom-input-group input:focus {
    outline: none;
    border-color: var(--accent-primary);
  }

  .error-text {
    font-size: 12px;
    color: var(--error);
  }

  /* Checkbox */
  .checkbox-label {
    display: flex;
    align-items: center;
    gap: 10px;
    cursor: pointer;
  }

  .checkbox-label input {
    width: 18px;
    height: 18px;
    accent-color: var(--accent-primary);
  }

  .checkbox-label span {
    font-size: 14px;
    color: var(--text-primary);
  }

  /* Select */
  select {
    padding: 10px 12px;
    background: var(--bg-tertiary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    color: var(--text-primary);
    font-size: 14px;
    cursor: pointer;
    max-width: 200px;
  }

  select:focus {
    outline: none;
    border-color: var(--accent-primary);
  }

  /* Dimension Inputs */
  .dimension-inputs {
    display: flex;
    align-items: flex-end;
    gap: 12px;
  }

  .dimension-separator {
    color: var(--text-muted);
    font-size: 18px;
    padding-bottom: 10px;
  }

  .input-group {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .input-group label {
    font-size: 13px;
    color: var(--text-secondary);
  }

  .input-group input {
    width: 100px;
    padding: 10px 12px;
    background: var(--bg-tertiary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    color: var(--text-primary);
    font-size: 14px;
  }

  .input-group input:focus {
    outline: none;
    border-color: var(--accent-primary);
  }

  /* Models Tab Styles */
  .model-config {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .input-row {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .input-row label {
    font-size: 13px;
    color: var(--text-secondary);
  }

  .input-row select,
  .input-row input[type="text"] {
    width: 100%;
    max-width: 400px;
    padding: 10px 12px;
    background: var(--bg-tertiary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    color: var(--text-primary);
    font-size: 14px;
  }

  .input-row select:focus,
  .input-row input[type="text"]:focus {
    outline: none;
    border-color: var(--accent-primary);
  }

  .model-actions {
    margin-top: 8px;
    padding-top: 16px;
    border-top: 1px solid var(--border-color);
  }

  .action-buttons {
    display: flex;
    gap: 12px;
    margin-bottom: 12px;
  }

  .result-message {
    padding: 10px 14px;
    border-radius: 8px;
    font-size: 13px;
    margin-bottom: 12px;
  }

  .result-message.success {
    background: rgba(34, 197, 94, 0.1);
    color: #22c55e;
    border: 1px solid rgba(34, 197, 94, 0.3);
  }

  .result-message.error {
    background: rgba(239, 68, 68, 0.1);
    color: #ef4444;
    border: 1px solid rgba(239, 68, 68, 0.3);
  }

  .result-message .duration {
    opacity: 0.7;
    margin-left: 4px;
  }

  .model-hint {
    font-size: 12px;
    color: var(--text-muted);
    line-height: 1.5;
    margin-top: 8px;
  }

  /* Footer */
  .settings-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 24px;
    border-top: 1px solid var(--border-color);
    background: var(--bg-tertiary);
    border-radius: 0 0 16px 16px;
  }

  .footer-right {
    display: flex;
    gap: 8px;
  }

  /* Buttons */
  .btn {
    padding: 10px 20px;
    font-size: 14px;
    font-weight: 500;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
    border: none;
  }

  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .btn-primary {
    background: var(--gradient-brand);
    color: white;
  }

  .btn-primary:hover:not(:disabled) {
    filter: brightness(1.1);
    box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
  }

  .btn-secondary {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    color: var(--text-secondary);
  }

  .btn-secondary:hover {
    background: var(--bg-tertiary);
    color: var(--text-primary);
  }

  .btn-ghost {
    background: transparent;
    color: var(--text-muted);
  }

  .btn-ghost:hover {
    color: var(--text-primary);
    background: var(--bg-tertiary);
  }

  .btn-danger {
    background: var(--error);
    color: white;
  }

  .btn-danger:hover {
    filter: brightness(1.1);
  }

  /* Confirm Overlay */
  .confirm-overlay {
    position: absolute;
    inset: 0;
    background: rgba(0, 0, 0, 0.7);
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 16px;
    animation: fadeIn 0.15s ease-out;
  }

  .confirm-dialog {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 24px;
    max-width: 400px;
    text-align: center;
    animation: slideIn 0.15s ease-out;
  }

  .confirm-dialog h3 {
    font-size: 18px;
    margin-bottom: 12px;
    color: var(--text-primary);
  }

  .confirm-dialog p {
    font-size: 14px;
    color: var(--text-secondary);
    margin-bottom: 20px;
    line-height: 1.5;
  }

  .confirm-actions {
    display: flex;
    justify-content: center;
    gap: 12px;
  }
</style>
