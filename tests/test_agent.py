import os
import pytest
from unittest.mock import MagicMock, patch
from src.agent import run_research

@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """Sets mock environment variables for the API keys."""
    monkeypatch.setenv("TAVILY_API_KEY", "mock-tavily-key")
    monkeypatch.setenv("GOOGLE_API_KEY", "mock-google-key")


@pytest.fixture
def mock_clients():
    """Mocks Tavily and Gemini clients to avoid external API calls."""
    with patch("src.agent.TavilyClient") as mock_tavily, \
         patch("src.agent.genai.Client") as mock_gemini:
        
        # Configure Tavily Client Mock
        tavily_instance = MagicMock()
        tavily_instance.search.return_value = {
            "results": [
                {
                    "title": "Mock Title 1",
                    "url": "https://mock1.com",
                    "content": "This is content from mock source 1."
                }
            ]
        }
        mock_tavily.return_value = tavily_instance
        
        # Configure Gemini Client Mock
        gemini_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "## Summary\nThis is a summary of findings [1].\n\n## Key Findings\n- Finding one.\n\n## Sources\n- [1] Mock Title 1: https://mock1.com"
        
        mock_usage = MagicMock()
        mock_usage.prompt_token_count = 100
        mock_usage.candidates_token_count = 200
        mock_response.usage_metadata = mock_usage
        
        gemini_instance.models.generate_content.return_value = mock_response
        mock_gemini.return_value = gemini_instance
        
        yield mock_tavily, mock_gemini


def test_output_not_empty(mock_clients):
    """Verifies that the generated research report file is created and is non-empty."""
    output_path = None
    try:
        output_path = run_research("What is NVIDIA's AI strategy?")
        
        # Verify the file is created
        assert os.path.exists(output_path), "The research output file was not created."
        
        # Verify it is not empty
        assert os.path.getsize(output_path) > 0, "The generated research output file is empty."
    finally:
        # Clean up created file
        if output_path and os.path.exists(output_path):
            os.remove(output_path)


def test_citations_present(mock_clients):
    """Verifies that the generated report contains inline citations such as [1]."""
    output_path = None
    try:
        output_path = run_research("What is the impact of quantum computing?")
        
        # Read file contents
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Verify citation is present in output content
        assert "[1]" in content, "No inline citation '[1]' found in the output report."
    finally:
        # Clean up created file
        if output_path and os.path.exists(output_path):
            os.remove(output_path)
