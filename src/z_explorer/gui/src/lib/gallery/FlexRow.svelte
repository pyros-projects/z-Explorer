<script lang="ts">
  /**
   * FlexRow Layout - Current default
   * Flexbox with aspect-aware growing for mixed aspect ratios
   */
  import { settings } from '../stores/settings';

  interface ImageData {
    url: string;
    prompt?: string;
    aspectRatio?: number;
  }

  export let images: ImageData[] = [];
  export let onSelect: (img: ImageData) => void;
  export let thumbnailHeight: number = 180;

  // Track loaded aspect ratios
  let imageAspects: Map<string, number> = new Map();

  function handleImageLoad(event: Event, img: ImageData) {
    const imgEl = event.target as HTMLImageElement;
    if (imgEl.naturalWidth && imgEl.naturalHeight) {
      const aspect = imgEl.naturalWidth / imgEl.naturalHeight;
      imageAspects.set(img.url, aspect);
      imageAspects = imageAspects; // trigger reactivity
    }
  }

  function getAspectRatio(img: ImageData): number {
    return imageAspects.get(img.url) || 1;
  }

  function getFlexGrow(img: ImageData): number {
    const aspect = getAspectRatio(img);
    return Math.max(0.5, Math.min(2, aspect));
  }
</script>

<div class="flex-row" style="--thumb-height: {thumbnailHeight}px">
  {#each images as img, i}
    <button
      class="image-card"
      on:click={() => onSelect(img)}
      style="animation-delay: {i * 50}ms; flex-grow: {getFlexGrow(img)};"
    >
      <img
        src={img.url}
        alt="Generated image {i + 1}"
        loading="lazy"
        on:load={(e) => handleImageLoad(e, img)}
      />
      <div class="image-overlay">
        {#if $settings.gallery.showPromptOnHover && img.prompt}
          <div class="prompt-preview">
            <p>{img.prompt}</p>
          </div>
        {:else}
          <span class="zoom-icon">🔍</span>
        {/if}
      </div>
    </button>
  {/each}
</div>

<style>
  .flex-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-content: flex-start;
  }

  .image-card {
    height: var(--thumb-height);
    min-width: 120px;
    max-width: 400px;
    flex-grow: 1;
    border-radius: var(--border-radius, 8px);
    overflow: hidden;
    cursor: pointer;
    border: none;
    padding: 0;
    background: var(--bg-tertiary, #1a1a2e);
    position: relative;
    animation: fadeIn 0.3s ease-out forwards;
    opacity: 0;
    transform: translateY(10px);
  }

  @keyframes fadeIn {
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .image-card img {
    display: block;
    height: 100%;
    width: 100%;
    object-fit: cover;
    transition: transform 0.3s ease;
  }

  .image-card:hover img {
    transform: scale(1.05);
  }

  .image-overlay {
    position: absolute;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    transition: opacity 0.2s;
  }

  .image-card:hover .image-overlay {
    opacity: 1;
  }

  .zoom-icon {
    font-size: 32px;
    filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
  }

  .prompt-preview {
    padding: 12px;
    text-align: left;
    overflow: hidden;
  }

  .prompt-preview p {
    margin: 0;
    font-size: 12px;
    line-height: 1.4;
    color: white;
    display: -webkit-box;
    -webkit-line-clamp: 4;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
  }
</style>
