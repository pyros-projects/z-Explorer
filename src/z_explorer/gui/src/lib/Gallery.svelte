<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { settings, thumbnailHeightPx } from './stores/settings';

  // Import layout components
  import FlexRow from './gallery/FlexRow.svelte';
  import MasonryVertical from './gallery/MasonryVertical.svelte';
  import MasonryHorizontal from './gallery/MasonryHorizontal.svelte';
  import GridSquare from './gallery/GridSquare.svelte';
  import GridAuto from './gallery/GridAuto.svelte';

  interface ImageData {
    url: string;
    prompt?: string;
    aspectRatio?: number;
  }

  export let images: ImageData[] = [];
  export let isGenerating = false;
  export let progress = 0;
  export let onOpenSettings: (() => void) | null = null;

  const dispatch = createEventDispatcher();

  function selectImage(img: ImageData) {
    dispatch('select', img);
  }

  function handleOpenSettings() {
    if (onOpenSettings) {
      onOpenSettings();
    }
  }
</script>

<div class="gallery">
  <div class="gallery-header">
    <div class="brand">
      <img src="/assets/icon.jpg" alt="Z" class="brand-icon" />
      <span class="brand-name">Z-Explorer</span>
    </div>
    <div class="header-right">
      {#if isGenerating}
        <div class="generating-badge">
          <span class="pulse"></span>
          Generating...
        </div>
      {/if}
      <h2>
        Gallery
        <span class="count">({images.length})</span>
      </h2>
      <button class="settings-btn" on:click={handleOpenSettings} title="Settings">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="3"></circle>
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
        </svg>
      </button>
    </div>
  </div>

  <div class="gallery-content">
    {#if isGenerating}
      <div class="generating-banner">
        <div class="spinner"></div>
        <span>Creating magic...</span>
        {#if progress > 0}
          <div class="progress-bar">
            <div class="progress-fill" style="width: {progress}%"></div>
          </div>
        {/if}
      </div>
    {/if}

    {#if images.length === 0 && !isGenerating}
      <div class="empty-state">
        <span class="empty-icon">✨</span>
        <h3>No images yet</h3>
        <p>Start generating with the CLI below</p>
      </div>
    {:else if images.length > 0}
      <div class="gallery-grid">
        {#if $settings.gallery.layout === 'flex-row'}
          <FlexRow {images} onSelect={selectImage} thumbnailHeight={$thumbnailHeightPx} />
        {:else if $settings.gallery.layout === 'masonry-vertical'}
          <MasonryVertical {images} onSelect={selectImage} />
        {:else if $settings.gallery.layout === 'masonry-horizontal'}
          <MasonryHorizontal {images} onSelect={selectImage} thumbnailHeight={$thumbnailHeightPx} />
        {:else if $settings.gallery.layout === 'grid-square'}
          <GridSquare {images} onSelect={selectImage} thumbnailHeight={$thumbnailHeightPx} />
        {:else if $settings.gallery.layout === 'grid-auto'}
          <GridAuto {images} onSelect={selectImage} thumbnailHeight={$thumbnailHeightPx} />
        {:else}
          <FlexRow {images} onSelect={selectImage} thumbnailHeight={$thumbnailHeightPx} />
        {/if}
      </div>
    {/if}
  </div>
</div>

<style>
  .gallery {
    height: 100%;
    display: flex;
    flex-direction: column;
    padding: 16px;
  }

  .gallery-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border-color);
  }

  .brand {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .brand-icon {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
  }

  .brand-name {
    font-size: 20px;
    font-weight: 700;
    background: linear-gradient(135deg, var(--accent-purple) 0%, var(--accent-cyan) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .gallery-header h2 {
    font-size: 16px;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--text-secondary);
  }

  .count {
    font-size: 14px;
    color: var(--text-muted);
    font-weight: 400;
  }

  .settings-btn {
    background: transparent;
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 8px;
    cursor: pointer;
    color: var(--text-muted);
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .settings-btn:hover {
    background: var(--bg-tertiary);
    color: var(--text-primary);
    border-color: var(--accent-primary);
  }

  .generating-badge {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
    background: var(--accent-glow);
    border: 1px solid var(--accent-primary);
    border-radius: 20px;
    font-size: 13px;
    color: var(--accent-secondary);
  }

  .pulse {
    width: 8px;
    height: 8px;
    background: var(--accent-primary);
    border-radius: 50%;
    animation: pulse 1.5s infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(1.2); }
  }

  .gallery-content {
    flex: 1;
    overflow-y: auto;
    padding-right: 8px;
  }

  .gallery-grid {
    height: 100%;
  }

  .generating-banner {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    padding: 12px 20px;
    margin-bottom: 16px;
    border-radius: var(--border-radius);
    background: linear-gradient(135deg, var(--bg-tertiary), var(--bg-secondary));
    border: 1px solid var(--accent-primary);
    color: var(--text-secondary);
    font-size: 14px;
  }

  .generating-banner .progress-bar {
    width: 120px;
  }

  .generating-banner .spinner {
    width: 20px;
    height: 20px;
    border-width: 2px;
  }

  .spinner {
    width: 40px;
    height: 40px;
    border: 3px solid var(--bg-tertiary);
    border-top-color: var(--accent-primary);
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .progress-bar {
    width: 80%;
    height: 4px;
    background: var(--bg-tertiary);
    border-radius: 2px;
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    background: var(--accent-primary);
    transition: width 0.3s ease;
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 60px 20px;
    color: var(--text-muted);
    text-align: center;
    height: 100%;
  }

  .empty-icon {
    font-size: 48px;
    margin-bottom: 16px;
    opacity: 0.5;
  }

  .empty-state h3 {
    font-size: 18px;
    margin-bottom: 8px;
    color: var(--text-secondary);
  }

  .empty-state p {
    font-size: 14px;
  }
</style>
