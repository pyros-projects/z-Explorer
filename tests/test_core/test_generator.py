"""Tests for z_explorer.core.generator module."""

from unittest.mock import patch, MagicMock

from z_explorer.core.types import GenerationRequest
from z_explorer.core.generator import (
    generate,
    _emit,
    _substitute_variables,
    _enhance_prompt,
)


# Patch target for image generator (imported inside generate function)
PATCH_IMAGE_GEN = "z_explorer.image_generator.generate_image"


class TestEmit:
    """Tests for the _emit helper function."""

    def test_emit_with_callback(self):
        """Test that emit calls the callback."""
        events = []

        def capture(event):
            events.append(event)

        _emit(capture, "starting", "Test message", 50, {"key": "value"})

        assert len(events) == 1
        assert events[0].stage == "starting"
        assert events[0].message == "Test message"
        assert events[0].progress == 50
        assert events[0].data == {"key": "value"}

    def test_emit_without_callback(self):
        """Test that emit works without callback (no-op)."""
        # Should not raise
        _emit(None, "starting", "Test message")


class TestSubstituteVariables:
    """Tests for _substitute_variables function."""

    def test_no_variables(self):
        """Test prompt without variables."""
        result = _substitute_variables("a cute cat", {})
        assert result == "a cute cat"

    def test_substitute_existing_variable(self, mock_current_dir, temp_library):
        """Test substituting an existing variable."""
        from z_explorer.models.prompt_vars import load_prompt_vars

        prompt_vars = load_prompt_vars()

        events = []
        result = _substitute_variables(
            "a cute __animal__",
            prompt_vars,
            on_progress=events.append,
            generate_missing=False,
        )

        # Should have substituted with one of: cat, dog, fox, rabbit
        assert "__animal__" not in result
        assert any(animal in result for animal in ["cat", "dog", "fox", "rabbit"])

        # Should have emitted substituting event
        assert any(e.stage == "substituting" for e in events)

    def test_multiple_same_variable(self, mock_current_dir, temp_library):
        """Test substituting same variable multiple times."""
        from z_explorer.models.prompt_vars import load_prompt_vars

        prompt_vars = load_prompt_vars()

        result = _substitute_variables(
            "__animal__ meets __animal__",
            prompt_vars,
            generate_missing=False,
        )

        # Both should be substituted (potentially different values)
        assert result.count("__animal__") == 0

    def test_subdirectory_variable(self, mock_current_dir, temp_library):
        """Test variable from subdirectory."""
        from z_explorer.models.prompt_vars import load_prompt_vars

        prompt_vars = load_prompt_vars()

        # Check that subdirectory variable was loaded
        assert any("fantasy" in key for key in prompt_vars.keys())

    def test_unknown_variable_no_generation(self, mock_current_dir, temp_library):
        """Test unknown variable without generation."""
        from z_explorer.models.prompt_vars import load_prompt_vars

        prompt_vars = load_prompt_vars()

        result = _substitute_variables(
            "a __nonexistent__ thing",
            prompt_vars,
            generate_missing=False,
        )

        # Should keep the variable as-is
        assert "__nonexistent__" in result


class TestEnhancePrompt:
    """Tests for _enhance_prompt function."""

    def test_enhance_calls_llm(self, mock_llm_provider):
        """Test that enhance calls the LLM provider."""
        events = []
        result = _enhance_prompt(
            "a cute cat",
            instruction="make it magical",
            on_progress=events.append,
        )

        assert "Enhanced:" in result
        assert any(e.stage == "enhancing" for e in events)
        assert any(e.stage == "enhanced" for e in events)


class TestGenerate:
    """Tests for the main generate function."""

    def test_generate_emits_starting(self, mock_all_models, sample_request):
        """Test that generate emits starting event."""
        events = []

        with patch(PATCH_IMAGE_GEN) as mock_gen:
            mock_gen.return_value = (MagicMock(), "/tmp/test.png")

            result = generate(sample_request, on_progress=events.append)

        # Check starting event was emitted
        starting_events = [e for e in events if e.stage == "starting"]
        assert len(starting_events) == 1
        assert starting_events[0].progress == 5

    def test_generate_loads_variables(self, mock_all_models, sample_request):
        """Test that generate loads prompt variables."""
        events = []

        with patch(PATCH_IMAGE_GEN) as mock_gen:
            mock_gen.return_value = (MagicMock(), "/tmp/test.png")

            result = generate(sample_request, on_progress=events.append)

        # Check loading_vars event was emitted
        loading_events = [e for e in events if e.stage == "loading_vars"]
        assert len(loading_events) == 1

    def test_generate_returns_result(self, mock_all_models, sample_request):
        """Test that generate returns a GenerationResult."""
        with patch(PATCH_IMAGE_GEN) as mock_gen:
            mock_gen.return_value = (MagicMock(), "/tmp/test.png")

            result = generate(sample_request)

        assert result.success is True
        assert len(result.images) == 1
        assert len(result.final_prompts) == 1
        assert len(result.seeds_used) == 1

    def test_generate_batch(self, mock_all_models, sample_request_batch):
        """Test batch generation with count > 1."""
        with patch(PATCH_IMAGE_GEN) as mock_gen:
            mock_gen.return_value = (MagicMock(), "/tmp/test.png")

            result = generate(sample_request_batch)

        assert result.success is True
        assert len(result.images) == 3
        assert len(result.final_prompts) == 3

    def test_generate_with_enhancement_syntax(self, mock_all_models):
        """Test generation with > enhancement syntax."""
        request = GenerationRequest(prompt="a cat > make it magical")

        events = []
        with patch(PATCH_IMAGE_GEN) as mock_gen:
            mock_gen.return_value = (MagicMock(), "/tmp/test.png")

            result = generate(request, on_progress=events.append)

        # Should have called enhancement
        enhancing_events = [e for e in events if e.stage == "enhancing"]
        assert len(enhancing_events) >= 1

    def test_generate_handles_image_error(self, mock_all_models, sample_request):
        """Test that generate handles image generation errors."""
        with patch(PATCH_IMAGE_GEN) as mock_gen:
            mock_gen.side_effect = RuntimeError("GPU out of memory")

            result = generate(sample_request)

        assert result.success is False
        assert len(result.errors) > 0
        assert "GPU out of memory" in result.errors[0]

    def test_generate_with_seed(self, mock_all_models):
        """Test generation with specific seed."""
        request = GenerationRequest(prompt="a cat", seed=12345)

        with patch(PATCH_IMAGE_GEN) as mock_gen:
            mock_gen.return_value = (MagicMock(), "/tmp/test.png")

            result = generate(request)

        assert result.seeds_used[0] == 12345

    def test_generate_progress_sequence(self, mock_all_models, sample_request):
        """Test that progress events follow logical sequence."""
        events = []

        with patch(PATCH_IMAGE_GEN) as mock_gen:
            mock_gen.return_value = (MagicMock(), "/tmp/test.png")

            generate(sample_request, on_progress=events.append)

        stages = [e.stage for e in events]

        # Should start with "starting"
        assert stages[0] == "starting"

        # Should end with "complete" or "error"
        assert stages[-1] in ("complete", "error")

        # Should have loading_vars before generating
        loading_idx = stages.index("loading_vars")
        assert loading_idx < len(stages) - 1

    def test_generate_without_callback(self, mock_all_models, sample_request):
        """Test generation without progress callback."""
        with patch(PATCH_IMAGE_GEN) as mock_gen:
            mock_gen.return_value = (MagicMock(), "/tmp/test.png")

            # Should not raise
            result = generate(sample_request, on_progress=None)

        assert result.success is True
