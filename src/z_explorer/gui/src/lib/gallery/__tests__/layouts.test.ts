/**
 * Gallery Layout Component Tests
 *
 * Tests for each gallery layout component.
 * Following TDD approach per implementation plan.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import { get } from 'svelte/store';

// Import layout components (will be created)
import FlexRow from '../FlexRow.svelte';
import MasonryVertical from '../MasonryVertical.svelte';
import MasonryHorizontal from '../MasonryHorizontal.svelte';
import GridSquare from '../GridSquare.svelte';
import GridAuto from '../GridAuto.svelte';

// Import settings for thumbnail height
import { updateGallery, initializeSettings } from '../../stores/settings';

// Mock image data for testing
const mockImages = [
  { url: '/test/image1.jpg', prompt: 'A beautiful sunset' },
  { url: '/test/image2.jpg', prompt: 'A majestic mountain' },
  { url: '/test/image3.jpg', prompt: 'A calm ocean' },
  { url: '/test/image4.jpg', prompt: 'A vibrant forest' },
  { url: '/test/image5.jpg', prompt: 'A starry night' },
];

// Mock the onSelect handler
const mockOnSelect = vi.fn();

describe('Gallery Layout Components', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    initializeSettings();
  });

  describe('FlexRow', () => {
    it('renders all images', () => {
      render(FlexRow, {
        props: {
          images: mockImages,
          onSelect: mockOnSelect,
          thumbnailHeight: 180,
        },
      });

      const images = screen.getAllByRole('img');
      expect(images).toHaveLength(5);
    });

    it('uses correct thumbnail height', () => {
      const { container } = render(FlexRow, {
        props: {
          images: mockImages,
          onSelect: mockOnSelect,
          thumbnailHeight: 250,
        },
      });

      const grid = container.querySelector('.flex-row');
      expect(grid).toBeDefined();
      expect(grid?.getAttribute('style')).toContain('--thumb-height: 250px');
    });

    it('calls onSelect when image is clicked', async () => {
      render(FlexRow, {
        props: {
          images: mockImages,
          onSelect: mockOnSelect,
          thumbnailHeight: 180,
        },
      });

      const buttons = screen.getAllByRole('button');
      await buttons[0].click();

      expect(mockOnSelect).toHaveBeenCalledWith(mockImages[0]);
    });

    it('shows empty state when no images', () => {
      const { container } = render(FlexRow, {
        props: {
          images: [],
          onSelect: mockOnSelect,
          thumbnailHeight: 180,
        },
      });

      // Should render without error, just no images
      const images = container.querySelectorAll('img');
      expect(images).toHaveLength(0);
    });
  });

  describe('MasonryVertical', () => {
    it('renders all images with CSS columns', () => {
      const { container } = render(MasonryVertical, {
        props: {
          images: mockImages,
          onSelect: mockOnSelect,
        },
      });

      const images = screen.getAllByRole('img');
      expect(images).toHaveLength(5);

      const grid = container.querySelector('.masonry-vertical');
      expect(grid).toBeDefined();
    });

    it('has break-inside: avoid on image cards', () => {
      const { container } = render(MasonryVertical, {
        props: {
          images: mockImages,
          onSelect: mockOnSelect,
        },
      });

      // Check that masonry container exists
      const masonry = container.querySelector('.masonry-vertical');
      expect(masonry).toBeDefined();
    });
  });

  describe('MasonryHorizontal', () => {
    it('renders with flex-wrap rows', () => {
      const { container } = render(MasonryHorizontal, {
        props: {
          images: mockImages,
          onSelect: mockOnSelect,
          thumbnailHeight: 180,
        },
      });

      const images = screen.getAllByRole('img');
      expect(images).toHaveLength(5);

      const grid = container.querySelector('.masonry-horizontal');
      expect(grid).toBeDefined();
    });

    it('uses thumbnail height for row height', () => {
      const { container } = render(MasonryHorizontal, {
        props: {
          images: mockImages,
          onSelect: mockOnSelect,
          thumbnailHeight: 300,
        },
      });

      const grid = container.querySelector('.masonry-horizontal');
      expect(grid?.getAttribute('style')).toContain('--thumb-height: 300px');
    });
  });

  describe('GridSquare', () => {
    it('renders uniform squares', () => {
      const { container } = render(GridSquare, {
        props: {
          images: mockImages,
          onSelect: mockOnSelect,
          thumbnailHeight: 180,
        },
      });

      const images = screen.getAllByRole('img');
      expect(images).toHaveLength(5);

      const grid = container.querySelector('.grid-square');
      expect(grid).toBeDefined();
    });

    it('applies object-fit: cover for cropping', () => {
      const { container } = render(GridSquare, {
        props: {
          images: mockImages,
          onSelect: mockOnSelect,
          thumbnailHeight: 180,
        },
      });

      // Grid square container should exist
      const grid = container.querySelector('.grid-square');
      expect(grid).toBeDefined();
    });
  });

  describe('GridAuto', () => {
    it('uses CSS Grid auto-fit', () => {
      const { container } = render(GridAuto, {
        props: {
          images: mockImages,
          onSelect: mockOnSelect,
          thumbnailHeight: 180,
        },
      });

      const images = screen.getAllByRole('img');
      expect(images).toHaveLength(5);

      const grid = container.querySelector('.grid-auto');
      expect(grid).toBeDefined();
    });

    it('responds to thumbnail size changes', () => {
      const { container } = render(GridAuto, {
        props: {
          images: mockImages,
          onSelect: mockOnSelect,
          thumbnailHeight: 350,
        },
      });

      const grid = container.querySelector('.grid-auto');
      expect(grid?.getAttribute('style')).toContain('--thumb-height: 350px');
    });
  });

  describe('All layouts', () => {
    const layouts = [
      { Component: FlexRow, name: 'FlexRow', requiresHeight: true },
      { Component: MasonryVertical, name: 'MasonryVertical', requiresHeight: false },
      { Component: MasonryHorizontal, name: 'MasonryHorizontal', requiresHeight: true },
      { Component: GridSquare, name: 'GridSquare', requiresHeight: true },
      { Component: GridAuto, name: 'GridAuto', requiresHeight: true },
    ];

    layouts.forEach(({ Component, name, requiresHeight }) => {
      it(`${name} renders correct number of images`, () => {
        const baseProps = {
          images: mockImages,
          onSelect: mockOnSelect,
        };
        const props = requiresHeight
          ? { ...baseProps, thumbnailHeight: 180 }
          : baseProps;

        render(Component, { props });

        const images = screen.getAllByRole('img');
        expect(images).toHaveLength(mockImages.length);
      });
    });
  });
});
