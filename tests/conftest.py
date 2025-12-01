"""Shared test fixtures for Z-Explorer tests."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from PIL import Image
import tempfile
import os


@pytest.fixture
def sample_request():
    """Sample generation request for testing."""
    from z_explorer.core.types import GenerationRequest
    return GenerationRequest(
        prompt="a cute __animal__",
        count=1,
        width=512,
        height=512,
    )


@pytest.fixture
def sample_request_batch():
    """Sample batch generation request."""
    from z_explorer.core.types import GenerationRequest
    return GenerationRequest(
        prompt="a __animal__ in __art_style__ style",
        count=3,
        width=512,
        height=512,
    )


@pytest.fixture
def sample_request_with_enhancement():
    """Sample request with enhancement."""
    from z_explorer.core.types import GenerationRequest
    return GenerationRequest(
        prompt="a cat > make it magical",
        count=1,
        width=512,
        height=512,
    )


@pytest.fixture
def temp_library(tmp_path):
    """Create temporary prompt variable library."""
    lib_path = tmp_path / "library"
    lib_path.mkdir()
    
    # Create sample variable files
    (lib_path / "animal.md").write_text("# Animals\ncat\ndog\nfox\nrabbit")
    (lib_path / "art_style.md").write_text("# Art styles\nwatercolor\noil painting\nsketch\ndigital art")
    (lib_path / "color.md").write_text("# Colors\nred\nblue\ngreen\ngolden")
    
    # Create subdirectory with variable
    sub_dir = lib_path / "fantasy"
    sub_dir.mkdir()
    (sub_dir / "creature.md").write_text("# Fantasy creatures\ndragon\nunicorn\nphoenix")
    
    return lib_path


@pytest.fixture
def mock_current_dir(tmp_path, temp_library):
    """Mock CURRENT_DIR to use temp library."""
    with patch('z_explorer.globals.CURRENT_DIR', str(tmp_path)):
        yield tmp_path


@pytest.fixture
def mock_image_generator():
    """Mock the image generator to avoid loading real models."""
    with patch('z_explorer.image_generator._pipeline') as mock_pipeline:
        # Create a mock image
        mock_image = Image.new('RGB', (512, 512), color='red')
        
        def mock_generate(prompt, width=1024, height=1024, seed=None, **kwargs):
            # Create temp file for the image
            fd, path = tempfile.mkstemp(suffix='.png')
            os.close(fd)
            mock_image.save(path)
            return mock_image, path
        
        with patch('z_explorer.image_generator.generate_image', side_effect=mock_generate):
            yield mock_pipeline


@pytest.fixture
def mock_llm_provider():
    """Mock the LLM provider to avoid loading real models."""
    with patch('z_explorer.llm_provider._model') as mock_model:
        mock_model.return_value = None
        
        def mock_enhance(prompt, instruction=""):
            return f"Enhanced: {prompt}"
        
        def mock_generate_vars(var_name, context, count=20):
            # Generate fake values based on variable name
            return [f"{var_name}_{i}" for i in range(count)]
        
        with patch('z_explorer.llm_provider.enhance_prompt', side_effect=mock_enhance):
            with patch('z_explorer.llm_provider.generate_prompt_variable_values', side_effect=mock_generate_vars):
                with patch('z_explorer.llm_provider.unload_model'):
                    yield mock_model


@pytest.fixture
def mock_all_models(mock_image_generator, mock_llm_provider, mock_current_dir):
    """Convenience fixture that mocks all heavy dependencies."""
    yield {
        'image_generator': mock_image_generator,
        'llm_provider': mock_llm_provider,
        'current_dir': mock_current_dir,
    }

