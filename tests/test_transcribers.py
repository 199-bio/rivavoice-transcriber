import pytest
import requests
from unittest.mock import patch, MagicMock
import os

from pyscribetranscribe.transcriber import (
    ElevenLabsTranscriber,
    ElevenLabsTranscriberError,
)
from rivavoice import constants  # Assuming constants are accessible

# Constants for testing
TEST_API_KEY = "test_elevenlabs_key"
TEST_FILE_PATH = "dummy_recording.wav"


# Fixture for the transcriber instance
@pytest.fixture
def elevenlabs_transcriber():
    # Create a dummy file for tests that need it
    with open(TEST_FILE_PATH, "w") as f:
        f.write("dummy audio data")
    yield ElevenLabsTranscriber(api_key=TEST_API_KEY)
    # Clean up dummy file
    if os.path.exists(TEST_FILE_PATH):
        os.remove(TEST_FILE_PATH)


@patch("requests.post")
def test_elevenlabs_transcribe_success(mock_post, elevenlabs_transcriber):
    """Test successful transcription with ElevenLabs."""
    # Mock the requests.post response
    mock_response = MagicMock()
    mock_response.status_code = 200
    # Correct key is 'text' based on transcriber code
    mock_response.json.return_value = {"text": "Hello world"}
    mock_post.return_value = mock_response

    result = elevenlabs_transcriber.transcribe_file(TEST_FILE_PATH)

    # Assertions
    assert result == "Hello world"
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == f"{constants.ELEVENLABS_API_URL}/{constants.ELEVENLABS_MODEL_ID}"
    assert kwargs["headers"]["xi-api-key"] == TEST_API_KEY
    assert "file" in kwargs["files"]  # Correct key for the file upload


@patch("requests.post")
def test_elevenlabs_transcribe_api_error(mock_post, elevenlabs_transcriber):
    """Test handling of API error (non-200 status) from ElevenLabs."""
    # Mock the requests.post response for an error
    mock_response = MagicMock()
    mock_response.status_code = 401  # Unauthorized
    mock_response.json.return_value = {"detail": {"message": "Invalid API Key"}}
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
        "401 Client Error", response=mock_response
    )
    mock_post.return_value = mock_response

    # Match the actual error format from transcriber.py
    with pytest.raises(ElevenLabsTranscriberError, match="API error 401"):
        elevenlabs_transcriber.transcribe_file(TEST_FILE_PATH)

    mock_post.assert_called_once()


@patch("requests.post")
def test_elevenlabs_transcribe_request_exception(mock_post, elevenlabs_transcriber):
    """Test handling of network/request exceptions during ElevenLabs call."""
    # Mock requests.post to raise a connection error
    mock_post.side_effect = requests.exceptions.ConnectionError("Network error")

    # Match the actual error format from transcriber.py
    with pytest.raises(ElevenLabsTranscriberError, match="Network error during transcription request"):
        elevenlabs_transcriber.transcribe_file(TEST_FILE_PATH)

    mock_post.assert_called_once()


def test_elevenlabs_transcribe_file_not_found(elevenlabs_transcriber):
    """Test handling when the input audio file doesn't exist."""
    # The code raises FileNotFoundError directly
    with pytest.raises(FileNotFoundError, match="Audio file not found"):
        elevenlabs_transcriber.transcribe_file("non_existent_file.wav")