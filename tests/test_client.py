from unittest.mock import AsyncMock, patch

import pytest

from shared_folder_opu.client import SharedFolderClient  # Replace with actual module name


@pytest.mark.asyncio
async def test_connection_establishment():
    with patch('asyncio.open_connection', new_callable=AsyncMock) as mock_open_conn:
        client = SharedFolderClient("/path/to/dir", "localhost", 8080)
        await client.client()
        mock_open_conn.assert_called_once()


@pytest.mark.asyncio
async def test_handle_server_sync():
    with patch('asyncio.open_connection', new_callable=AsyncMock) as mock_open_conn:
        with patch.object(SharedFolderClient, 'handle_sync', new_callable=AsyncMock) as mock_handle_sync:
            client = SharedFolderClient("/path/to/dir", "localhost", 8080)
            mock_open_conn.return_value = (AsyncMock(), AsyncMock())
            await client.client()
            mock_handle_sync.assert_called()


@pytest.mark.asyncio
async def test_handle_server_file():
    with patch('asyncio.open_connection', new_callable=AsyncMock) as mock_open_conn:
        with patch.object(SharedFolderClient, 'handle_server_file', new_callable=AsyncMock) as mock_handle_file:
            client = SharedFolderClient("/path/to/dir", "localhost", 8080)
            mock_open_conn.return_value = (AsyncMock(), AsyncMock())
            await client.client()
            mock_handle_file.assert_not_called()  # Adjust as per the expected behavior

# Additional setup or teardown can be added as needed
