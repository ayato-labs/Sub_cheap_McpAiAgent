import pytest
from mcp_ai_worker.utils import is_safe_url, fetch_and_clean_markdown
from unittest.mock import MagicMock, patch


def test_is_safe_url():
    # Positive cases
    assert is_safe_url("https://google.com") is True
    assert is_safe_url("https://github.com") is True

    # Negative cases
    assert is_safe_url("http://google.com") is False  # Only https
    assert is_safe_url("ftp://google.com") is False
    assert is_safe_url("not-a-url") is False

    # SSRF / Private IP cases
    with patch("socket.gethostbyname") as mock_gethost:
        mock_gethost.return_value = "127.0.0.1"
        assert is_safe_url("https://localhost") is False

        mock_gethost.return_value = "10.0.0.1"
        assert is_safe_url("https://internal.corp") is False

        mock_gethost.return_value = "192.168.1.1"
        assert is_safe_url("https://router.local") is False


def test_fetch_and_clean_markdown_security():
    with pytest.raises(ValueError, match="Security Error"):
        fetch_and_clean_markdown("http://insecure.com")


@patch("httpx.Client.get")
def test_fetch_and_clean_markdown_success(mock_get):
    # Mock HTML response
    mock_response = MagicMock()
    mock_response.text = """
    <html>
        <body>
            <nav>Nav noise</nav>
            <main>
                <h1>Main Title</h1>
                <p>This is the core content. We need to make it longer than 100 characters to avoid the SPA detection failure. Adding some more text here to ensure the test passes and the cleaning logic works as expected.</p>
                <footer>Footer noise</footer>
            </main>
            <script>alert(1)</script>
        </body>
    </html>
    """
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    result = fetch_and_clean_markdown("https://example.com")

    assert "# Main Title" in result
    assert "This is the core content." in result
    assert "Nav noise" not in result
    assert "Footer noise" not in result
    assert "alert(1)" not in result


@patch("httpx.Client.get")
def test_fetch_and_clean_markdown_spa_failure(mock_get):
    # Mock HTML response with very little content in body/main
    mock_response = MagicMock()
    mock_response.text = "<html><body><div id='app'></div></body></html>"
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    with pytest.raises(ValueError, match="Extraction Error: Content is too short"):
        fetch_and_clean_markdown("https://spa-site.com")
