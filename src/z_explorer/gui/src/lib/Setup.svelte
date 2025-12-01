<script lang="ts">
  import { createEventDispatcher, onMount, onDestroy } from 'svelte';

  export let apiBase: string = '';
  
  const dispatch = createEventDispatcher();

  interface DownloadProgress {
    model_name: string;
    repo_id: string;
    status: string;
    current_file?: string;
    files_done: number;
    files_total: number;
    bytes_done: number;
    bytes_total: number;
    progress_percent: number;
    speed_mbps: number;
    eta_seconds?: number;
    error?: string;
  }

  interface ModelInfo {
    name: string;
    repo_id: string;
  }

  let isLoading = true;
  let isDownloading = false;
  let downloadComplete = false;
  let hasError = false;
  let errorMessage = '';
  
  let modelsNeeded: ModelInfo[] = [];
  let modelsDownloaded: Record<string, boolean> = {};
  let currentProgress: DownloadProgress | null = null;
  let completedModels: string[] = [];
  
  let eventSource: EventSource | null = null;
  let receivedFinalStatus = false;  // Track if we got a proper completion/error status

  function formatBytes(bytes: number): string {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  function formatTime(seconds: number | undefined): string {
    if (!seconds || seconds <= 0) return '--:--';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }

  async function checkSetupStatus() {
    try {
      const res = await fetch(`${apiBase}/api/setup/status`);
      if (res.ok) {
        const data = await res.json();
        modelsNeeded = data.models_needed || [];
        modelsDownloaded = data.models_downloaded || {};
        
        const allDownloaded = modelsNeeded.every(m => modelsDownloaded[m.name]);
        if (allDownloaded && modelsNeeded.length > 0) {
          downloadComplete = true;
        }
      }
    } catch (e) {
      console.error('Failed to check setup status:', e);
    } finally {
      isLoading = false;
    }
  }

  function startDownload() {
    if (isDownloading) return;

    isDownloading = true;
    hasError = false;
    errorMessage = '';
    completedModels = [];
    receivedFinalStatus = false;
    
    eventSource = new EventSource(`${apiBase}/api/setup/download`);
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.status === 'all_complete' || data.status === 'error') {
          receivedFinalStatus = true;  // Mark that we got a proper final status
          downloadComplete = data.success;
          hasError = !data.success;
          // Capture error message from final status (don't overwrite if already set)
          if (!data.success && data.message && !errorMessage) {
            errorMessage = data.message;
          }
          isDownloading = false;
          eventSource?.close();
          return;
        }
        
        currentProgress = data as DownloadProgress;
        
        if (data.status === 'complete' && data.model_name) {
          if (!completedModels.includes(data.model_name)) {
            completedModels = [...completedModels, data.model_name];
          }
        }
        
        if (data.status === 'error' && data.error) {
          hasError = true;
          errorMessage = data.error;
          isDownloading = false;
          eventSource?.close();
        }
      } catch (e) {
        console.error('Failed to parse download progress:', e);
      }
    };
    
    eventSource.onerror = (error) => {
      // SSE fires onerror when connection closes, even on normal completion
      // Only treat as error if we didn't receive a proper final status
      if (!receivedFinalStatus) {
        console.error('Download SSE error:', error);
        hasError = true;
        errorMessage = 'Connection to server lost';
        isDownloading = false;
      }
      eventSource?.close();
    };
  }

  function handleContinue() {
    dispatch('complete');
  }

  function handleRetry() {
    hasError = false;
    errorMessage = '';
    startDownload();
  }

  onMount(() => {
    checkSetupStatus();
  });

  onDestroy(() => {
    eventSource?.close();
  });
</script>

<div class="setup-container">
  <div class="setup-card">
    <div class="header">
      <img src="/assets/icon.jpg" alt="Z-Explorer" class="logo-img" />
      <h1>Z-Explorer</h1>
      <p class="subtitle">Local AI Image Generation</p>
    </div>

    {#if isLoading}
      <div class="loading-state">
        <div class="spinner"></div>
        <p>Initializing...</p>
      </div>
    {:else if downloadComplete}
      <div class="complete-state">
        <div class="success-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
        </div>
        <h2>Ready to Create</h2>
        <p>All models downloaded. Let's make some art.</p>
        <button class="primary-btn" on:click={handleContinue}>
          <span>Start Creating</span>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M5 12h14M12 5l7 7-7 7"/>
          </svg>
        </button>
      </div>
    {:else if hasError}
      <div class="error-state">
        <div class="error-icon">!</div>
        <h2>Download Failed</h2>
        <p class="error-message">{errorMessage || 'An error occurred'}</p>
        <button class="primary-btn" on:click={handleRetry}>
          Retry Download
        </button>
      </div>
    {:else if isDownloading}
      <div class="download-state">
        <h2>Downloading Models</h2>
        
        {#if currentProgress}
          <div class="current-model">
            <div class="model-header">
              <span class="model-name">{currentProgress.model_name}</span>
              <span class="model-status">{currentProgress.status}</span>
            </div>
            
            <div class="progress-bar-container">
              <div
                class="progress-bar"
                class:indeterminate={currentProgress.progress_percent < 1 && currentProgress.status === 'downloading'}
                style="width: {currentProgress.progress_percent > 0 ? currentProgress.progress_percent : 100}%"
              ></div>
            </div>

            <div class="progress-details">
              <span class="progress-percent">
                {#if currentProgress.progress_percent > 0}
                  {currentProgress.progress_percent.toFixed(1)}%
                {:else}
                  Downloading...
                {/if}
              </span>
              {#if currentProgress.bytes_total > 0}
                <span class="progress-size">
                  {formatBytes(currentProgress.bytes_done)} / {formatBytes(currentProgress.bytes_total)}
                </span>
              {/if}
              {#if currentProgress.speed_mbps > 0}
                <span class="progress-speed">{currentProgress.speed_mbps.toFixed(1)} MB/s</span>
              {/if}
              {#if currentProgress.eta_seconds}
                <span class="progress-eta">ETA: {formatTime(currentProgress.eta_seconds)}</span>
              {/if}
            </div>
            
            {#if currentProgress.current_file}
              <div class="current-file">{currentProgress.current_file}</div>
            {/if}
          </div>
        {/if}
        
        <div class="models-list">
          {#each modelsNeeded as model}
            <div class="model-item" class:completed={completedModels.includes(model.name)} class:active={currentProgress?.model_name === model.name}>
              <span class="model-check">
                {#if completedModels.includes(model.name)}
                  ✓
                {:else if currentProgress?.model_name === model.name}
                  ●
                {:else}
                  ○
                {/if}
              </span>
              <span class="model-label">{model.name}</span>
            </div>
          {/each}
        </div>
        
        <p class="download-hint">
          This may take several minutes depending on your connection
        </p>
      </div>
    {:else}
      <div class="ready-state">
        <h2>Models Required</h2>
        <p class="info-text">
          Z-Explorer needs to download AI models (~5-10 GB) to generate images locally.
        </p>
        
        <div class="models-list">
          {#each modelsNeeded as model}
            <div class="model-item" class:downloaded={modelsDownloaded[model.name]}>
              <span class="model-check">
                {modelsDownloaded[model.name] ? '✓' : '○'}
              </span>
              <div class="model-info">
                <span class="model-label">{model.name}</span>
                <span class="model-repo">{model.repo_id}</span>
              </div>
            </div>
          {/each}
        </div>
        
        <button class="primary-btn" on:click={startDownload}>
          <span>Download Models</span>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/>
          </svg>
        </button>
        
        <p class="storage-hint">
          Models are cached locally for offline use
        </p>
      </div>
    {/if}
  </div>
  
  <div class="bg-glow"></div>
  <div class="bg-glow-2"></div>
</div>

<style>
  .setup-container {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    background: var(--bg-primary);
    padding: 20px;
    position: relative;
    overflow: hidden;
  }

  /* Animated background glows */
  .bg-glow {
    position: absolute;
    width: 600px;
    height: 600px;
    background: radial-gradient(circle, rgba(168, 85, 247, 0.15) 0%, transparent 70%);
    top: -200px;
    left: -200px;
    animation: float 20s ease-in-out infinite;
    pointer-events: none;
  }

  .bg-glow-2 {
    position: absolute;
    width: 500px;
    height: 500px;
    background: radial-gradient(circle, rgba(34, 211, 238, 0.1) 0%, transparent 70%);
    bottom: -150px;
    right: -150px;
    animation: float 25s ease-in-out infinite reverse;
    pointer-events: none;
  }

  @keyframes float {
    0%, 100% { transform: translate(0, 0); }
    50% { transform: translate(50px, 30px); }
  }

  .setup-card {
    background: linear-gradient(135deg, rgba(20, 20, 30, 0.95) 0%, rgba(15, 15, 25, 0.98) 100%);
    border: 1px solid rgba(139, 92, 246, 0.2);
    border-radius: 20px;
    padding: 48px;
    max-width: 480px;
    width: 100%;
    box-shadow: 
      0 25px 80px -20px rgba(0, 0, 0, 0.6),
      0 0 60px rgba(139, 92, 246, 0.08),
      inset 0 1px 0 rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(20px);
    position: relative;
    z-index: 1;
  }

  .header {
    text-align: center;
    margin-bottom: 36px;
  }

  .logo-img {
    width: 80px;
    height: 80px;
    border-radius: 20px;
    margin-bottom: 20px;
    box-shadow: 0 10px 40px rgba(139, 92, 246, 0.3);
    animation: pulse-glow 3s ease-in-out infinite;
  }

  @keyframes pulse-glow {
    0%, 100% { box-shadow: 0 10px 40px rgba(139, 92, 246, 0.3); }
    50% { box-shadow: 0 10px 50px rgba(34, 211, 238, 0.4); }
  }

  h1 {
    margin: 0;
    font-size: 32px;
    font-weight: 700;
    background: linear-gradient(135deg, #f0f0f5 0%, #a0a0b0 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.5px;
  }

  .subtitle {
    margin: 8px 0 0;
    color: var(--text-muted);
    font-size: 14px;
    letter-spacing: 0.5px;
  }

  h2 {
    margin: 0 0 16px;
    font-size: 22px;
    font-weight: 600;
    color: var(--text-primary);
  }

  /* Loading State */
  .loading-state {
    text-align: center;
    padding: 40px 0;
  }

  .spinner {
    width: 48px;
    height: 48px;
    border: 3px solid rgba(139, 92, 246, 0.2);
    border-top-color: var(--accent-purple);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 16px;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .loading-state p {
    color: var(--text-secondary);
  }

  /* Complete State */
  .complete-state {
    text-align: center;
    padding: 20px 0;
  }

  .success-icon {
    width: 72px;
    height: 72px;
    border-radius: 50%;
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 20px;
    animation: scaleIn 0.5s ease-out;
  }

  .success-icon svg {
    width: 36px;
    height: 36px;
  }

  @keyframes scaleIn {
    from { transform: scale(0); }
    to { transform: scale(1); }
  }

  .complete-state p {
    color: var(--text-secondary);
    margin-bottom: 28px;
  }

  /* Error State */
  .error-state {
    text-align: center;
    padding: 20px 0;
  }

  .error-icon {
    width: 72px;
    height: 72px;
    border-radius: 50%;
    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
    color: white;
    font-size: 36px;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 20px;
  }

  .error-message {
    color: #f87171;
    font-size: 14px;
    margin-bottom: 24px;
    padding: 14px;
    background: rgba(239, 68, 68, 0.1);
    border-radius: 10px;
    border: 1px solid rgba(239, 68, 68, 0.2);
  }

  /* Ready State */
  .ready-state {
    text-align: center;
  }

  .info-text {
    color: var(--text-secondary);
    margin-bottom: 24px;
    line-height: 1.6;
  }

  /* Download State */
  .download-state h2 {
    text-align: center;
    margin-bottom: 28px;
  }

  .current-model {
    background: rgba(139, 92, 246, 0.08);
    border: 1px solid rgba(139, 92, 246, 0.15);
    border-radius: 14px;
    padding: 18px;
    margin-bottom: 24px;
  }

  .model-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 14px;
  }

  .model-name {
    font-weight: 600;
    color: var(--text-primary);
  }

  .model-status {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--accent-cyan);
    background: rgba(34, 211, 238, 0.15);
    padding: 4px 10px;
    border-radius: 6px;
  }

  .progress-bar-container {
    height: 6px;
    background: rgba(139, 92, 246, 0.15);
    border-radius: 3px;
    overflow: hidden;
    margin-bottom: 14px;
  }

  .progress-bar {
    height: 100%;
    background: linear-gradient(90deg, var(--accent-purple) 0%, var(--accent-cyan) 100%);
    border-radius: 3px;
    transition: width 0.3s ease;
    position: relative;
  }

  .progress-bar::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
    animation: shimmer 1.5s infinite;
  }

  @keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
  }

  /* Indeterminate progress bar animation when we don't have real progress data */
  .progress-bar.indeterminate {
    background: linear-gradient(
      90deg,
      var(--accent-purple) 0%,
      var(--accent-cyan) 25%,
      var(--accent-purple) 50%,
      var(--accent-cyan) 75%,
      var(--accent-purple) 100%
    );
    background-size: 200% 100%;
    animation: indeterminate-flow 2s linear infinite;
  }

  @keyframes indeterminate-flow {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
  }

  .progress-details {
    display: flex;
    flex-wrap: wrap;
    gap: 14px;
    font-size: 12px;
    color: var(--text-secondary);
  }

  .progress-percent {
    font-weight: 600;
    color: var(--accent-cyan);
  }

  .current-file {
    margin-top: 10px;
    font-size: 11px;
    color: var(--text-muted);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  /* Models List */
  .models-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-bottom: 24px;
  }

  .model-item {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 14px 18px;
    background: rgba(20, 20, 30, 0.6);
    border: 1px solid rgba(100, 100, 120, 0.15);
    border-radius: 12px;
    transition: all 0.2s;
  }

  .model-item.active {
    border-color: rgba(139, 92, 246, 0.4);
    background: rgba(139, 92, 246, 0.08);
  }

  .model-item.completed,
  .model-item.downloaded {
    border-color: rgba(16, 185, 129, 0.3);
    background: rgba(16, 185, 129, 0.08);
  }

  .model-check {
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    font-size: 14px;
    color: var(--text-muted);
  }

  .model-item.active .model-check {
    color: var(--accent-purple);
    animation: pulse 1s ease-in-out infinite;
  }

  .model-item.completed .model-check,
  .model-item.downloaded .model-check {
    color: #10b981;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }

  .model-info {
    display: flex;
    flex-direction: column;
    gap: 3px;
  }

  .model-label {
    color: var(--text-primary);
    font-weight: 500;
  }

  .model-repo {
    font-size: 11px;
    color: var(--text-muted);
    font-family: var(--font-mono);
  }

  /* Primary Button */
  .primary-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    padding: 16px 32px;
    background: linear-gradient(135deg, var(--accent-purple) 0%, var(--accent-cyan) 100%);
    border: none;
    border-radius: 12px;
    color: white;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.25s;
    width: 100%;
    position: relative;
    overflow: hidden;
  }

  .primary-btn::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
    transition: left 0.5s;
  }

  .primary-btn:hover::before {
    left: 100%;
  }

  .primary-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 15px 40px rgba(139, 92, 246, 0.4);
  }

  .primary-btn:active {
    transform: translateY(0);
  }

  .primary-btn svg {
    width: 20px;
    height: 20px;
    transition: transform 0.2s;
  }

  .primary-btn:hover svg {
    transform: translateX(4px);
  }

  /* Hints */
  .download-hint,
  .storage-hint {
    text-align: center;
    font-size: 12px;
    color: var(--text-muted);
    margin-top: 20px;
  }
</style>
