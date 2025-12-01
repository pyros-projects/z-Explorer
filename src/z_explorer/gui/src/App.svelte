<script lang="ts">
  import './app.css';
  import Gallery from './lib/Gallery.svelte';
  import FakeCLI from './lib/FakeCLI.svelte';
  import Setup from './lib/Setup.svelte';
  import Settings from './lib/Settings.svelte';
  import { settings, initializeSettings, updateCLI } from './lib/stores/settings';
  import { onMount, onDestroy } from 'svelte';

  // Backend configuration - dynamically resolve based on where UI is hosted
  function getApiBase(): string {
    // In browser environment
    if (typeof window !== 'undefined') {
      const { protocol, hostname, port } = window.location;
      
      // Development mode with Vite dev server (port 5173) - use proxy (relative URLs)
      if (port === '5173') {
        return '';  // Vite proxy handles /api/* routes
      }
      
      // Production or hosted mode - use same origin as the UI
      // This handles RunPod, remote servers, custom ports, etc.
      return `${protocol}//${hostname}${port ? ':' + port : ''}`;
    }
    
    // Fallback for SSR or non-browser environments
    return 'http://127.0.0.1:8345';
  }
  
  const API_BASE = getApiBase();

  // Image data structure with URL and optional prompt
  interface ImageData {
    url: string;
    prompt?: string;
  }

  let images: ImageData[] = [];
  let isGenerating = false;
  let progress = 0;
  let currentPrompt = '';
  let selectedImage: ImageData | null = null;

  let isTauriAvailable = false;
  let isBackendConnected = false;
  let statusMessage = '';
  let needsSetup = false;
  let checkingSetup = true;
  let showSettings = false;

  // Open/close settings dialog
  function openSettings() {
    showSettings = true;
  }

  function closeSettings() {
    showSettings = false;
  }

  // Function to convert file paths to Tauri asset URLs
  let convertFileSrc: ((path: string) => string) | null = null;

  // CLI component reference
  let cliComponent: FakeCLI;

  // SSE connection for progress updates
  let eventSource: EventSource | null = null;

  // Resizable panel state - use settings as initial value, then allow resizing
  let cliHeight = $settings.cli.height;
  let isResizing = false;
  let minCliHeight = 150;
  let maxCliHeight = 600;
  let cliHistoryVisible = $settings.cli.showHistory;

  // Handle CLI history toggle
  function handleHistoryToggle(event: CustomEvent<{ visible: boolean }>) {
    cliHistoryVisible = event.detail.visible;
  }

  // Sync CLI height from settings when settings change (but not during resize)
  $: if (!isResizing && $settings.cli.height !== cliHeight) {
    cliHeight = $settings.cli.height;
  }

  // Check if running in Tauri and set up event listeners
  async function checkTauri() {
    try {
      const { invoke } = await import('@tauri-apps/api/core');
      const tauri = await import('@tauri-apps/api/core');
      const { listen } = await import('@tauri-apps/api/event');
      convertFileSrc = tauri.convertFileSrc;
      await invoke('list_images');
      isTauriAvailable = true;

      // Listen for progress events from Rust backend
      listen<{ message: string; progress: number | null; stage: string }>('generation-progress', (event) => {
        const { message, progress: prog, stage } = event.payload;

        // Update progress bar
        if (prog !== null) {
          progress = prog;
        }

        // Add message to CLI
        if (cliComponent) {
          const isError = stage === 'error';
          cliComponent.addResult(message, isError);
        }

        // Auto-show image when it's ready (extract path from message)
        if (stage === 'image_ready' && message.includes('Saved: ')) {
          const path = message.replace('💾 Saved: ', '');
          const displayUrl = toDisplayUrl(path);
          // Show preview of the new image
          selectedImage = { url: displayUrl };
        }
      });

      return true;
    } catch {
      isTauriAvailable = false;
      return false;
    }
  }

  // Check if Python backend is running
  async function checkBackend(): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE}/api/health`, { signal: AbortSignal.timeout(2000) });
      return res.ok;
    } catch {
      return false;
    }
  }

  // Check if models need to be downloaded
  async function checkSetupStatus(): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE}/api/setup/status`);
      if (res.ok) {
        const data = await res.json();
        // If not configured or models not downloaded, show setup
        if (!data.is_configured) {
          return true;
        }
        // Check if any required model is not downloaded
        const modelsNeeded = data.models_needed || [];
        const modelsDownloaded = data.models_downloaded || {};
        return modelsNeeded.some((m: any) => !modelsDownloaded[m.name]);
      }
    } catch (e) {
      console.log('Could not check setup status:', e);
    }
    return false;
  }

  function handleSetupComplete() {
    needsSetup = false;
    loadImages();
  }

  // Resize handlers
  function startResize(e: MouseEvent) {
    isResizing = true;
    document.addEventListener('mousemove', doResize);
    document.addEventListener('mouseup', stopResize);
    e.preventDefault();
  }

  function doResize(e: MouseEvent) {
    if (!isResizing) return;
    const container = document.querySelector('.app') as HTMLElement;
    if (!container) return;

    const containerRect = container.getBoundingClientRect();
    const newHeight = containerRect.bottom - e.clientY;
    cliHeight = Math.max(minCliHeight, Math.min(maxCliHeight, newHeight));
  }

  function stopResize() {
    isResizing = false;
    document.removeEventListener('mousemove', doResize);
    document.removeEventListener('mouseup', stopResize);
    // Save the new height to settings store so it persists
    updateCLI({ height: cliHeight });
  }

  // Convert file paths to displayable URLs
  function toDisplayUrl(path: string): string {
    // Safety check for null/undefined path
    if (!path) {
      console.warn('🔄 [toDisplayUrl] Empty path received');
      return '';
    }
    
    // For Tauri mode
    if (typeof convertFileSrc === 'function' && !path.startsWith('http')) {
      try {
        return convertFileSrc(path);
      } catch (e) {
        console.warn('🔄 [toDisplayUrl] Tauri convertFileSrc failed:', e);
      }
    }
    
    // Already a full URL
    if (path.startsWith('http')) {
      return path;
    }
    
    // Relative URL from API - prepend base
    if (path.startsWith('/output/')) {
      return `${API_BASE}${path}`;
    }
    
    // For browser mode, extract filename and use static file server
    if (path.includes('output')) {
      const filename = path.split(/[/\\]/).pop();
      return `${API_BASE}/output/${filename}`;
    }
    
    return path;
  }

  // Handle generation via HTTP API with SSE progress
  async function handleGenerateHttp(prompt: string, params: any, seed: number | null) {
    isGenerating = true;
    progress = 0;

    // Start progress tracking in CLI
    if (cliComponent) {
      cliComponent.startGeneration();
    }

    // Build query params
    const queryParams = new URLSearchParams({
      prompt,
      count: String(params.count || 1),
      width: String(params.width || 1024),
      height: String(params.height || 1024),
    });
    if (seed !== null) {
      queryParams.set('seed', String(seed));
    }

    console.log('🎬 [GENERATE] Starting generation...');
    console.log('📝 [GENERATE] Prompt:', prompt);
    console.log('⚙️ [GENERATE] Params:', params);
    console.log('🎲 [GENERATE] Seed:', seed);

    try {
      // Connect to SSE endpoint for progress
      const sseUrl = `${API_BASE}/api/generate/stream?${queryParams}`;
      console.log('🔗 [SSE] Connecting to:', sseUrl);
      eventSource = new EventSource(sseUrl);
      let eventCount = 0;

      eventSource.onopen = () => {
        console.log('✅ [SSE] Connection opened');
      };

      eventSource.onerror = (err) => {
        console.error('❌ [SSE] Connection error:', err);
      };

      eventSource.onmessage = (event) => {
        eventCount++;
        console.log(`📨 [SSE] Event #${eventCount}:`, event.data);
        
        try {
          const data = JSON.parse(event.data);
          console.log(`📦 [SSE] Parsed event:`, {
            stage: data.stage,
            message: data.message,
            progress: data.progress,
            path: data.path,
            final_prompts: data.final_prompts
          });
          
          // Update Gallery progress bar
          if (data.progress !== undefined && data.progress !== null) {
            console.log(`📊 [PROGRESS] Updating to ${data.progress}%`);
            progress = data.progress;
          }

          // Update FakeCLI progress bar with stage info
          if (cliComponent && data.stage && data.stage !== 'complete' && data.stage !== 'error') {
            console.log(`🔄 [CLI] Updating progress: ${data.stage} (${data.progress}%)`);
            cliComponent.updateProgress(
              data.progress || 0,
              data.stage,
              data.message || ''
            );
          }

          // Image saved - add to gallery and show preview
          if (data.stage === 'image_saved' && data.path) {
            try {
              console.log(`🖼️ [IMAGE] Raw path from event:`, data.path);
              const displayUrl = toDisplayUrl(data.path);
              console.log(`🖼️ [IMAGE] Converted URL:`, displayUrl);
              // Get prompt from data if available
              const imagePrompt = data.data?.prompt || undefined;
              const imageData: ImageData = { url: displayUrl, prompt: imagePrompt };
              images = [imageData, ...images];
              console.log(`🖼️ [IMAGE] Added to gallery, setting preview...`);
              selectedImage = imageData;
              console.log(`🖼️ [IMAGE] Preview set to:`, selectedImage);
            } catch (imgErr) {
              console.error('❌ [IMAGE] Error handling image_saved:', imgErr);
            }
          }

          // Show substituted prompts
          if (data.stage === 'substituting') {
            console.log(`🔀 [SUBSTITUTE] ${data.message}`);
          }

          // Generation complete
          if (data.stage === 'complete') {
            console.log('✅ [COMPLETE] Generation finished!');
            console.log('📝 [COMPLETE] Final prompts:', data.final_prompts);
            console.log('🖼️ [COMPLETE] Images:', data.images);
            isGenerating = false;
            progress = 0;
            if (cliComponent) {
              cliComponent.completeGeneration(true);
              cliComponent.addResult(`✅ ${data.message || 'Generation complete!'}`);
              // Show the final prompt if variable was substituted
              if (data.final_prompts && data.final_prompts.length > 0) {
                const finalPrompt = data.final_prompts[0];
                if (finalPrompt !== prompt) {
                  cliComponent.addResult(`📝 Final prompt: ${finalPrompt}`);
                }
              }
            }
            eventSource?.close();
            loadImages();
          }

          // Error
          if (data.stage === 'error') {
            console.error('❌ [ERROR]', data.message);
            isGenerating = false;
            progress = 0;
            if (cliComponent) {
              cliComponent.completeGeneration(false);
              cliComponent.addResult(data.message || 'Generation failed', true);
            }
            eventSource?.close();
          }
        } catch (e) {
          console.error('❌ [SSE] Failed to parse event:', e, 'Raw:', event.data);
        }
      };

      eventSource.onerror = (error) => {
        console.error('SSE error:', error);
        isGenerating = false;
        progress = 0;
        if (cliComponent) {
          cliComponent.addResult('❌ Connection to server lost', true);
        }
        eventSource?.close();
      };

    } catch (error) {
      console.error('Generation failed:', error);
      statusMessage = `❌ Generation failed: ${error}`;
      isGenerating = false;
      progress = 0;
    }
  }

  // Handle generation from CLI
  async function handleGenerate(event: CustomEvent) {
    const { prompt, params, seed } = event.detail;
    currentPrompt = prompt;
    statusMessage = '';

    if (isTauriAvailable) {
      // Use Tauri invoke
      isGenerating = true;
      progress = 0;

      try {
        const { invoke } = await import('@tauri-apps/api/core');

        const result = await invoke('generate_image', {
          prompt,
          count: params.count || 1,
          width: params.width || 1024,
          height: params.height || 1024,
          seed: seed || null,
        });

        if (Array.isArray(result)) {
          // Convert file paths to ImageData objects for display
          const convertedImages: ImageData[] = (result as string[]).map(path => ({
            url: toDisplayUrl(path)
          }));
          images = [...convertedImages, ...images];
        }
      } catch (error) {
        console.error('Generation failed:', error);
        statusMessage = `❌ Generation failed: ${error}`;
      } finally {
        isGenerating = false;
        progress = 0;
      }
    } else if (isBackendConnected) {
      // Use HTTP API with SSE
      await handleGenerateHttp(prompt, params, seed);
    } else {
      // Demo mode
      statusMessage = '⚠️ No backend connected. Start with: z-explorer';
      if (cliComponent) {
        cliComponent.addResult('⚠️ Server not running. Start with: z-explorer', true);
      }
    }
  }

  // Handle GPU info request
  async function handleGpuInfo(): Promise<any> {
    if (isTauriAvailable) {
      try {
        const { invoke } = await import('@tauri-apps/api/core');
        return await invoke('get_gpu_info');
      } catch (e) {
        console.error('Failed to get GPU info:', e);
        return null;
      }
    } else if (isBackendConnected) {
      try {
        const res = await fetch(`${API_BASE}/api/gpu`);
        if (res.ok) {
          return await res.json();
        }
      } catch (e) {
        console.error('Failed to get GPU info:', e);
      }
    }
    return null;
  }

  // Handle model unload request
  async function handleUnload(): Promise<any> {
    if (isTauriAvailable) {
      try {
        const { invoke } = await import('@tauri-apps/api/core');
        return await invoke('unload_models');
      } catch (e) {
        console.error('Failed to unload models:', e);
        return null;
      }
    } else if (isBackendConnected) {
      try {
        const res = await fetch(`${API_BASE}/api/unload`, { method: 'POST' });
        if (res.ok) {
          return await res.json();
        }
      } catch (e) {
        console.error('Failed to unload models:', e);
      }
    }
    return null;
  }

  // Handle list variables request
  async function handleListVariables(): Promise<any> {
    console.log('📚 [App] handleListVariables called, tauri:', isTauriAvailable);
    
    if (isTauriAvailable) {
      try {
        const { invoke } = await import('@tauri-apps/api/core');
        return await invoke('list_variables');
      } catch (e) {
        console.error('Failed to list variables:', e);
        return null;
      }
    }
    
    // Try HTTP API (don't require isBackendConnected - it might not be set yet)
    try {
      console.log('📚 [App] Fetching variables from:', `${API_BASE}/api/variables`);
      const res = await fetch(`${API_BASE}/api/variables`);
      if (res.ok) {
        const data = await res.json();
        console.log('📚 [App] Variables loaded:', data);
        return data;
      } else {
        console.warn('📚 [App] Variables fetch failed:', res.status);
      }
    } catch (e) {
      console.warn('📚 [App] Variables fetch error (server might not be running):', e);
    }
    return null;
  }

  function handleImageSelect(event: CustomEvent) {
    console.log('🖼️ [handleImageSelect] Event detail:', event.detail);
    console.log('🖼️ [handleImageSelect] Prompt:', event.detail?.prompt);
    selectedImage = event.detail;
  }

  function closePreview() {
    selectedImage = null;
  }

  // Load images from server
  async function loadImages() {
    try {
      const res = await fetch(`${API_BASE}/api/images`);
      if (res.ok) {
        const data = await res.json();
        if (data.images) {
          images = data.images.map((img: any) => {
            // Always prepend API_BASE for browser mode
            let url: string;
            if (img.url) {
              url = img.url.startsWith('http') ? img.url : `${API_BASE}${img.url}`;
            } else {
              url = `${API_BASE}/output/${img.name}`;
            }
            return { url, prompt: img.prompt || undefined };
          });
        }
      }
    } catch (e) {
      console.log('Could not load images:', e);
    }
  }

  // Load existing images on mount
  onMount(async () => {
    // Initialize settings from localStorage
    initializeSettings();

    const hasTauri = await checkTauri();
    
    if (hasTauri) {
      statusMessage = '🖥️ Running in native Tauri mode';
      checkingSetup = false;
      try {
        const { invoke } = await import('@tauri-apps/api/core');
        const loadedPaths: string[] = await invoke('list_images');
        // Convert file paths to ImageData objects for display
        images = loadedPaths.map(path => ({ url: toDisplayUrl(path) }));
      } catch (e) {
        console.log('Failed to load images:', e);
      }
    } else {
      // Check for Python backend
      isBackendConnected = await checkBackend();
      
      if (isBackendConnected) {
        // Check if setup/download is needed
        needsSetup = await checkSetupStatus();
        checkingSetup = false;
        
        if (!needsSetup) {
          const displayUrl = API_BASE || window.location.origin;
          statusMessage = `✅ Connected to Z-Explorer server (${displayUrl})`;
          await loadImages();
          // Fetch and display the actual version from backend
          if (cliComponent) {
            await cliComponent.fetchVersion(API_BASE);
          }
        }
      } else {
        checkingSetup = false;
        statusMessage = '🎨 Offline mode - Start server with: z-explorer';
      }
    }
  });

  onDestroy(() => {
    // Clean up SSE connection
    eventSource?.close();
  });
</script>

{#if checkingSetup}
  <div class="loading-screen">
    <div class="loading-spinner"></div>
    <p>Connecting to server...</p>
  </div>
{:else if needsSetup && isBackendConnected}
  <Setup apiBase={API_BASE} on:complete={handleSetupComplete} />
{:else}
<main class="app" class:resizing={isResizing}>
  {#if statusMessage}
    <div class="status-bar">{statusMessage}</div>
  {/if}

  <div class="gallery-container">
    <Gallery
      {images}
      {isGenerating}
      {progress}
      onOpenSettings={openSettings}
      on:select={handleImageSelect}
    />

    {#if selectedImage}
      <!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
      <div class="preview-overlay" role="dialog" aria-modal="true" on:click={closePreview} on:keydown={(e) => e.key === 'Escape' && closePreview()}>
        {#if isGenerating}
          <div class="preview-generating">
            <span class="pulse"></span>
            <span>Generating...</span>
            {#if progress > 0}
              <div class="preview-progress">
                <div class="preview-progress-fill" style="width: {progress}%"></div>
              </div>
            {/if}
          </div>
        {/if}
        <div class="preview-content" on:click|stopPropagation>
          <img src={selectedImage.url} alt="Preview" class="preview-image" />
          {#if selectedImage.prompt}
            <div class="preview-prompt">
              <span class="prompt-label">📜 Prompt</span>
              <p class="prompt-text">{selectedImage.prompt}</p>
            </div>
          {/if}
        </div>
        <button class="close-btn" on:click={closePreview}>×</button>
      </div>
    {/if}
  </div>

  <!-- svelte-ignore a11y-no-static-element-interactions -->
  {#if cliHistoryVisible}
    <div class="resize-handle" on:mousedown={startResize}>
      <div class="handle-line"></div>
    </div>
  {/if}

  <div class="cli-container" class:collapsed={!cliHistoryVisible} style={cliHistoryVisible ? `height: ${cliHeight}px` : ''}>
    <FakeCLI
      bind:this={cliComponent}
      {isGenerating}
      isTauriAvailable={isTauriAvailable || isBackendConnected}
      on:generate={handleGenerate}
      on:historyToggle={handleHistoryToggle}
      getGpuInfo={handleGpuInfo}
      unloadModels={handleUnload}
      listVariables={handleListVariables}
      {openSettings}
    />
  </div>

  <!-- Settings Dialog -->
  <Settings open={showSettings} onClose={closeSettings} />
</main>
{/if}

<style>
  .loading-screen {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100vh;
    background: var(--bg-primary);
    color: var(--text-secondary);
    position: relative;
    overflow: hidden;
  }

  .loading-screen::before {
    content: '';
    position: absolute;
    width: 400px;
    height: 400px;
    background: radial-gradient(circle, rgba(168, 85, 247, 0.1) 0%, transparent 70%);
    top: -100px;
    left: -100px;
    animation: float 15s ease-in-out infinite;
  }

  .loading-screen::after {
    content: '';
    position: absolute;
    width: 300px;
    height: 300px;
    background: radial-gradient(circle, rgba(34, 211, 238, 0.08) 0%, transparent 70%);
    bottom: -50px;
    right: -50px;
    animation: float 20s ease-in-out infinite reverse;
  }

  @keyframes float {
    0%, 100% { transform: translate(0, 0); }
    50% { transform: translate(30px, 20px); }
  }

  .loading-spinner {
    width: 48px;
    height: 48px;
    border: 3px solid rgba(139, 92, 246, 0.2);
    border-top-color: var(--accent-purple);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 16px;
    position: relative;
    z-index: 1;
  }

  .loading-screen p {
    position: relative;
    z-index: 1;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .app {
    display: flex;
    flex-direction: column;
    height: 100vh;
    background: var(--bg-primary);
  }

  .status-bar {
    padding: 10px 16px;
    background: linear-gradient(90deg, var(--bg-tertiary) 0%, var(--bg-secondary) 50%, var(--bg-tertiary) 100%);
    border-bottom: 1px solid var(--border-color);
    font-size: 13px;
    color: var(--text-secondary);
    text-align: center;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
  }

  .gallery-container {
    flex: 1;
    overflow: hidden;
    position: relative;
  }

  .cli-container {
    min-height: 150px;
    max-height: 600px;
    background: var(--bg-secondary);
    flex: none;
  }

  .cli-container.collapsed {
    min-height: 0;
    height: auto !important;
  }

  .resize-handle {
    height: 8px;
    background: var(--bg-tertiary);
    cursor: ns-resize;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.2s;
    flex-shrink: 0;
  }

  .resize-handle:hover,
  .app.resizing .resize-handle {
    background: linear-gradient(90deg, var(--accent-purple), var(--accent-cyan));
  }

  .handle-line {
    width: 50px;
    height: 4px;
    background: var(--border-color);
    border-radius: 2px;
    transition: all 0.2s;
  }

  .resize-handle:hover .handle-line,
  .app.resizing .handle-line {
    background: white;
    box-shadow: 0 0 10px rgba(139, 92, 246, 0.5);
  }

  .app.resizing {
    cursor: ns-resize;
    user-select: none;
  }

  .preview-overlay {
    position: absolute;
    inset: 0;
    background: rgba(0, 0, 0, 0.95);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    z-index: 100;
    cursor: pointer;
    animation: fadeIn 0.2s ease-out;
    overflow: hidden;
    padding: 20px;
    box-sizing: border-box;
  }

  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  .preview-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    max-width: 100%;
    max-height: 100%;
    overflow: hidden;
  }

  .preview-image {
    max-width: 100%;
    max-height: calc(100% - 140px);
    object-fit: contain;
    border-radius: var(--border-radius);
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
    flex-shrink: 1;
  }

  .preview-prompt {
    margin-top: 12px;
    background: linear-gradient(135deg, rgba(10, 10, 20, 0.9) 0%, rgba(15, 15, 25, 0.85) 100%);
    border: 1px solid rgba(139, 92, 246, 0.3);
    border-radius: var(--border-radius);
    padding: 10px 16px;
    max-width: 700px;
    max-height: 120px;
    overflow-y: auto;
    backdrop-filter: blur(10px);
    animation: fadeSlideUp 0.3s ease-out;
    flex-shrink: 0;
  }

  .preview-prompt .prompt-label {
    display: block;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #22c55e;
    margin-bottom: 8px;
  }

  .preview-prompt .prompt-text {
    margin: 0;
    color: #f1f5f9;
    font-size: 13px;
    line-height: 1.5;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
  }

  @keyframes fadeSlideUp {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .close-btn {
    position: absolute;
    top: 12px;
    right: 12px;
    width: 36px;
    height: 36px;
    border: none;
    background: var(--bg-tertiary);
    color: var(--text-primary);
    font-size: 20px;
    border-radius: 50%;
    cursor: pointer;
    transition: all 0.2s;
    opacity: 0.8;
  }

  .close-btn:hover {
    background: var(--accent-primary);
    transform: scale(1.1);
    opacity: 1;
  }

  /* Generating indicator on preview overlay */
  .preview-generating {
    position: absolute;
    top: 16px;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 20px;
    background: rgba(10, 10, 15, 0.9);
    border: 1px solid var(--accent-primary);
    border-radius: 24px;
    color: var(--text-secondary);
    font-size: 14px;
    backdrop-filter: blur(8px);
    z-index: 10;
    animation: fadeIn 0.2s ease-out;
  }

  .preview-generating .pulse {
    width: 10px;
    height: 10px;
    background: var(--accent-primary);
    border-radius: 50%;
    animation: pulse 1.5s infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(1.2); }
  }

  .preview-progress {
    width: 80px;
    height: 4px;
    background: var(--bg-tertiary);
    border-radius: 2px;
    overflow: hidden;
  }

  .preview-progress-fill {
    height: 100%;
    background: var(--gradient-brand);
    transition: width 0.3s ease;
  }
</style>
