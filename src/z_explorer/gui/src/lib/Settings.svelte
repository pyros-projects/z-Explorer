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
  let reloadResult: { status: string; message?: string; duration_ms?: number } | null = null;
  let loadingServerConfig = false;

  // Download state
  let isDownloading = false;
  let downloadProgress: {
    model_name: string;
    status: string;
    progress_percent: number;
    current_file?: string;
    speed_mbps?: number;
    eta_seconds?: number;
    error?: string;
  } | null = null;
  let downloadError: string | null = null;
  let modelsToDownload: { image_repo?: string; llm_repo?: string } | null = null;

  // Fetch current model config from server
  async function fetchServerConfig() {
    loadingServerConfig = true;
    try {
      const response = await fetch('/api/config');
      if (response.ok) {
        const config = await response.json();
        // Update local state with server config
        imageMode = config.image_mode || 'hf_download';
        llmMode = config.llm_mode || 'hf_download';

        // Set repo/path based on mode
        if (config.image_mode === 'hf_download' || config.image_mode === 'sdnq') {
          imageRepo = config.image_model || '';
          imagePath = '';
        } else {
          imagePath = config.image_model || '';
          imageRepo = '';
        }

        if (config.llm_mode === 'hf_download') {
          llmRepo = config.llm_model || '';
          llmPath = '';
        } else if (config.llm_mode === 'z_image') {
          llmRepo = '';
          llmPath = '';
        } else {
          llmPath = config.llm_model || '';
          llmRepo = '';
        }
      }
    } catch (e) {
      console.warn('Could not fetch server config:', e);
    } finally {
      loadingServerConfig = false;
    }
  }

  // Check if selected models need downloading
  async function checkModelsNeedDownload(): Promise<{ image_repo?: string; llm_repo?: string } | null> {
    try {
      const response = await fetch('/api/settings/models/check-cache', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          image_mode: imageMode,
          image_repo: imageRepo || null,
          llm_mode: llmMode,
          llm_repo: llmRepo || null,
        }),
      });

      if (response.ok) {
        const result = await response.json();
        if (result.needs_download) {
          return {
            image_repo: !result.image_cached ? result.image_repo : undefined,
            llm_repo: !result.llm_cached ? result.llm_repo : undefined,
          };
        }
      }
    } catch (e) {
      console.warn('Could not check model cache:', e);
    }
    return null;
  }

  // Download models with progress
  async function downloadModels(repos: { image_repo?: string; llm_repo?: string }): Promise<boolean> {
    isDownloading = true;
    downloadProgress = null;
    downloadError = null;

    return new Promise((resolve) => {
      const params = new URLSearchParams();
      if (repos.image_repo) params.set('image_repo', repos.image_repo);
      if (repos.llm_repo) params.set('llm_repo', repos.llm_repo);

      const eventSource = new EventSource(`/api/settings/models/download?${params}`);

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          // Final status event
          if (data.status === 'all_complete') {
            eventSource.close();
            isDownloading = false;
            downloadProgress = null;
            resolve(true);
            return;
          }

          if (data.status === 'error' && data.success === false) {
            eventSource.close();
            isDownloading = false;
            downloadError = data.message || 'Download failed';
            resolve(false);
            return;
          }

          // Progress update
          downloadProgress = {
            model_name: data.model_name || '',
            status: data.status || '',
            progress_percent: data.progress_percent || 0,
            current_file: data.current_file,
            speed_mbps: data.speed_mbps,
            eta_seconds: data.eta_seconds,
            error: data.error,
          };

          if (data.error) {
            downloadError = data.error;
          }
        } catch (e) {
          console.error('Error parsing download progress:', e);
        }
      };

      eventSource.onerror = () => {
        eventSource.close();
        isDownloading = false;
        downloadError = 'Connection to server lost';
        resolve(false);
      };
    });
  }

  // Initialize local settings when dialog opens
  $: if (open) {
    localSettings = structuredClone($settings);
    activeTab = 'gallery';
    thumbnailError = '';
    showResetConfirm = false;
    // Reset model states
    testResult = null;
    reloadResult = null;
    // Reset download states
    isDownloading = false;
    downloadProgress = null;
    downloadError = null;
    modelsToDownload = null;
    // Fetch current config from server (will update model fields)
    fetchServerConfig();
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

  // Handle Save - checks if models need download first
  async function handleSave() {
    if (hasErrors || isDownloading) return;

    // Check if we're on Models tab and models need downloading
    if (activeTab === 'models') {
      const needsDownload = await checkModelsNeedDownload();
      if (needsDownload && (needsDownload.image_repo || needsDownload.llm_repo)) {
        modelsToDownload = needsDownload;
        // Start download - dialog stays open
        const success = await downloadModels(needsDownload);
        if (!success) {
          // Download failed - stay on dialog to show error
          return;
        }
        // Download succeeded - apply model config and reload
        await applyModelConfigAndReload();
      }
    }

    // Commit changes to store
    updateGallery(localSettings.gallery);
    updateCLI(localSettings.cli);
    updateGeneration(localSettings.generation);

    onClose();
  }

  // Apply model configuration to server and reload models
  async function applyModelConfigAndReload() {
    try {
      // Update server config
      await fetch('/api/settings/models', {
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

      // Reload models
      await fetch('/api/models/reload', { method: 'POST' });

      // Update local settings store
      localSettings.models = {
        imageMode,
        imageRepo,
        imagePath,
        llmMode,
        llmRepo,
        llmPath,
      };
    } catch (e) {
      console.error('Failed to apply model config:', e);
    }
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

            <!-- Show History by Default -->
            <div class="setting-group">
              <label class="checkbox-label">
                <input
                  type="checkbox"
                  bind:checked={localSettings.cli.showHistory}
                />
                <span>Show history by default</span>
              </label>
              <p class="setting-hint">When disabled, only the input line and progress bar are visible. Toggle with the ☰ button.</p>
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
            {#if loadingServerConfig}
              <div class="loading-config">
                <span class="spinner"></span>
                <span>Loading current configuration...</span>
              </div>
            {/if}
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

              <!-- Download Progress UI -->
              {#if isDownloading && downloadProgress}
                <div class="download-progress-container">
                  <div class="download-header">
                    <span class="download-icon">⬇️</span>
                    <span class="download-title">Downloading {downloadProgress.model_name}</span>
                  </div>
                  <div class="download-progress-bar">
                    <div
                      class="download-progress-fill"
                      style="width: {downloadProgress.progress_percent}%"
                    ></div>
                  </div>
                  <div class="download-stats">
                    <span class="download-percent">{downloadProgress.progress_percent.toFixed(1)}%</span>
                    {#if downloadProgress.speed_mbps}
                      <span class="download-speed">{downloadProgress.speed_mbps.toFixed(1)} MB/s</span>
                    {/if}
                    {#if downloadProgress.eta_seconds}
                      <span class="download-eta">~{Math.ceil(downloadProgress.eta_seconds)}s remaining</span>
                    {/if}
                  </div>
                  {#if downloadProgress.current_file}
                    <div class="download-file">{downloadProgress.current_file}</div>
                  {/if}
                </div>
              {/if}

              {#if downloadError}
                <div class="result-message error">
                  ✗ Download failed: {downloadError}
                </div>
              {/if}
            </div>
          </div>
        {/if}
      </div>

      <!-- Footer -->
      <div class="settings-footer">
        <button class="btn btn-secondary" on:click={handleResetClick} disabled={isDownloading}>
          Reset to Defaults
        </button>
        <div class="footer-right">
          <button class="btn btn-ghost" on:click={handleCancel} disabled={isDownloading}>
            Cancel
          </button>
          <button class="btn btn-primary" on:click={handleSave} disabled={hasErrors || isDownloading}>
            {#if isDownloading}
              Downloading...
            {:else}
              Save
            {/if}
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

  .setting-hint {
    font-size: 12px;
    color: var(--text-muted);
    margin: 4px 0 0 28px;
    line-height: 1.4;
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
  .loading-config {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 16px;
    background: rgba(139, 92, 246, 0.1);
    border: 1px solid rgba(139, 92, 246, 0.3);
    border-radius: 8px;
    color: var(--text-secondary);
    font-size: 13px;
    margin-bottom: 16px;
  }

  .spinner {
    width: 16px;
    height: 16px;
    border: 2px solid rgba(139, 92, 246, 0.3);
    border-top-color: var(--accent-primary);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

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

  /* Download Progress Styles */
  .download-progress-container {
    margin-top: 16px;
    padding: 16px;
    background: linear-gradient(135deg, rgba(34, 211, 238, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
    border: 1px solid rgba(34, 211, 238, 0.3);
    border-radius: 12px;
    animation: fadeIn 0.3s ease-out;
  }

  .download-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
  }

  .download-icon {
    font-size: 18px;
    animation: bounce 1s ease infinite;
  }

  @keyframes bounce {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-3px); }
  }

  .download-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .download-progress-bar {
    height: 8px;
    background: var(--bg-tertiary);
    border-radius: 4px;
    overflow: hidden;
    margin-bottom: 8px;
  }

  .download-progress-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--accent-cyan), var(--accent-purple));
    border-radius: 4px;
    transition: width 0.3s ease;
    position: relative;
  }

  .download-progress-fill::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(
      90deg,
      transparent 0%,
      rgba(255, 255, 255, 0.2) 50%,
      transparent 100%
    );
    animation: shimmer 1.5s infinite;
  }

  @keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
  }

  .download-stats {
    display: flex;
    gap: 16px;
    font-size: 12px;
    color: var(--text-secondary);
    margin-bottom: 4px;
  }

  .download-percent {
    font-weight: 600;
    color: var(--accent-cyan);
  }

  .download-speed {
    color: var(--text-muted);
  }

  .download-eta {
    color: var(--text-muted);
  }

  .download-file {
    font-size: 11px;
    color: var(--text-muted);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    font-family: 'JetBrains Mono', monospace;
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
