# test_server_handlers.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from shared_folder_opu.server_handlers import handle_delete_file


@pytest.mark.asyncio
@patch("os.path.exists")
@patch("os.unlink")
@patch("os.path.isdir")
@patch("shutil.rmtree")
@patch("shared_folder_opu.general_utils.get_local_file_path", new_callable=AsyncMock)
async def test_handle_delete_file(mock_get_local_file_path, mock_rmtree, mock_isdir, mock_unlink, mock_exists):
    test_file_path = '/test/folder/path/to/file'
    mock_get_local_file_path.return_value = test_file_path
    mock_exists.return_value = True
    mock_isdir.return_value = False

    reader = MagicMock()

    await handle_delete_file(reader, '/test/folder')

    mock_get_local_file_path.assert_called_once()
    mock_exists.assert_called_once_with(test_file_path)
    mock_isdir.assert_called_once_with(test_file_path)
    mock_unlink.assert_called_once_with(test_file_path)
    mock_rmtree.assert_not_called()
