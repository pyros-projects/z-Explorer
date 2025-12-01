<script lang="ts">
  /**
   * MasonryVertical Layout
   * Pinterest-style columns with variable heights
   * Best for portrait-heavy galleries
   */
  import { settings } from '../stores/settings';

  interface ImageData {
    url: string;
    prompt?: string;
    aspectRatio?: number;
  }

  export let images: ImageData[] = [];
  export let onSelect: (img: ImageData) => void;
</script>

<div class="masonry-vertical">
  {#each images as img, i}
    <button
      class="image-card"
      on:click={() => onSelect(img)}
      style="animation-delay: {i * 50}ms"
    >
      <img
        src={img.url}
        alt="Generated image {i + 1}"
        loading="lazy"
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
  .masonry-vertical {
    columns: 3;
    column-gap: 8px;
  }

  .image-card {
    break-inside: avoid;
    margin-bottom: 8px;
    width: 100%;
    border: none;
    padding: 0;
    cursor: pointer;
    border-radius: var(--border-radius, 8px);
    overflow: hidden;
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
    width: 100%;
    height: auto;
    display: block;
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

  /* Responsive columns */
  @media (max-width: 1400px) {
    .masonry-vertical {
      columns: 3;
    }
  }
  @media (max-width: 1000px) {
    .masonry-vertical {
      columns: 2;
    }
  }
  @media (max-width: 600px) {
    .masonry-vertical {
      columns: 1;
    }
  }
</style>
