import asyncio
import os.path
import struct
import pytest

from unittest.mock import AsyncMock, patch, MagicMock

from shared_folder_opu.protocol import MessageType, UserEditTypes
from shared_folder_opu.server import SharedFolderServer


@pytest.mark.asyncio
@patch("os.path.exists")
@patch("os.unlink")
@patch("os.path.isdir")
@patch("shutil.rmtree")
async def test_handle_delete_file(mock_rmtree, mock_isdir, mock_unlink, mock_exists):
    test_file_path = '/tmp/server'
    server = SharedFolderServer("localhost", 1234, test_file_path)
    mock_exists.return_value = True
    mock_isdir.return_value = False
    file_name = "a"

    writer = MagicMock()
    reader = AsyncMock()
    reader.readexactly = asyncio.coroutine(
        AsyncMock(side_effect=[
            struct.pack(">B", UserEditTypes.DELETE.value),
            struct.pack(f">H", len(file_name)),
            struct.pack(f">{len(file_name)}s", file_name.encode())
        ])
    )

    await server.handle_message(MessageType.USER_EDIT, reader, writer)

    mock_exists.assert_called_once_with(os.path.join(test_file_path, file_name).encode())
    mock_isdir.assert_called_once_with(os.path.join(test_file_path, file_name).encode())
    mock_unlink.assert_called_once_with(os.path.join(test_file_path, file_name).encode())
    mock_rmtree.assert_not_called()


@pytest.mark.asyncio
@patch("os.path.exists")
@patch("os.mkdir")
@patch("os.open")
async def test_handle_create_dir(mock_open, mock_mkdir, mock_exists):
    test_file_path = '/tmp/server'
    server = SharedFolderServer("localhost", 1234, test_file_path)
    mock_exists.return_value = False
    dir_name = "my_dir"

    writer = MagicMock()
    reader = AsyncMock()
    reader.readexactly = asyncio.coroutine(
        AsyncMock(side_effect=[
            struct.pack(">B", UserEditTypes.CREATE.value),
            struct.pack(f">H", len(dir_name)),
            struct.pack(f">{len(dir_name)}s", dir_name.encode()),
            struct.pack(">B", True)
        ])
    )

    await server.handle_message(MessageType.USER_EDIT, reader, writer)

    mock_exists.assert_called_once()
    mock_mkdir.assert_called_once_with(os.path.join(test_file_path, dir_name).encode())
    mock_open.assert_not_called()


@pytest.mark.asyncio
@patch("os.path.exists")
@patch("os.mkdir")
@patch("os.open")
async def test_handle_create_file(mock_open, mock_mkdir, mock_exists):
    test_file_path = '/tmp/server'
    server = SharedFolderServer("localhost", 1234, test_file_path)
    mock_exists.return_value = False
    dir_name = "my_file"

    writer = MagicMock()
    reader = AsyncMock()
    reader.readexactly = asyncio.coroutine(
        AsyncMock(side_effect=[
            struct.pack(">B", UserEditTypes.CREATE.value),
            struct.pack(f">H", len(dir_name)),
            struct.pack(f">{len(dir_name)}s", dir_name.encode()),
            struct.pack(">B", False)
        ])
    )

    await server.handle_message(MessageType.USER_EDIT, reader, writer)

    mock_exists.assert_called_once()
    mock_mkdir.assert_not_called()
    mock_open.assert_called_once_with(os.path.join(test_file_path, dir_name).encode(), os.O_CREAT)


@pytest.mark.asyncio
@patch("os.path.exists")
@patch("os.mkdir")
@patch("os.open")
async def test_handle_create_file_when_exists(mock_open, mock_mkdir, mock_exists):
    test_file_path = '/tmp/server'
    server = SharedFolderServer("localhost", 1234, test_file_path)
    mock_exists.return_value = True
    dir_name = "my_file"

    writer = MagicMock()
    reader = AsyncMock()
    reader.readexactly = asyncio.coroutine(
        AsyncMock(side_effect=[
            struct.pack(">B", UserEditTypes.CREATE.value),
            struct.pack(f">H", len(dir_name)),
            struct.pack(f">{len(dir_name)}s", dir_name.encode()),
            struct.pack(">B", False)
        ])
    )

    await server.handle_message(MessageType.USER_EDIT, reader, writer)

    mock_exists.assert_called_once()
    mock_mkdir.assert_not_called()
    mock_open.assert_not_called()


@pytest.mark.asyncio
@patch("json.dumps")
@patch('hashlib.md5')
@patch("builtins.open")
@patch("os.unlink")
async def test_handle_modify(mock_unlink, mock_open, mock_md5, mock_dumps):
    test_file_path = '/tmp/server1'
    server = SharedFolderServer("localhost", 1234, test_file_path)
    file_name = "my_file"
    content = "BEST FILE EVER"

    mock_dumps.return_value = ""
    mock_md5.hexdigest.return_value = "\x00" * 32
    writer = MagicMock()
    reader = AsyncMock()
    reader.readexactly = asyncio.coroutine(
        AsyncMock(side_effect=[
            struct.pack(">B", UserEditTypes.MODIFY.value),
            struct.pack(">H", len(file_name)),
            struct.pack(f">{len(file_name)}s", file_name.encode()),
            struct.pack(">H", len(content)),
            struct.pack(f">{len(content)}s", content.encode())
        ])
    )

    await server.handle_message(MessageType.USER_EDIT, reader, writer)

    mock_unlink.assert_called_once_with(os.path.join(test_file_path, file_name).encode())
    mock_open.assert_called_with(os.path.join(test_file_path, file_name).encode(), "w")
