import os
import struct

from logger_singleton import SingletonLogger
from protocol import UserEditMessage, UserEditTypes, UserRequestResponse, StatusTypes, \
    UserEditResponse
from directory_utils import calculate_md5
from general_utils import get_string, get_local_file_path

logger = SingletonLogger.get_logger()


async def handle_delete_file(reader, folder_path):
    full_path = await get_local_file_path(reader, folder_path.encode())
    assert os.path.exists(full_path), f"{full_path} does not exist"
    logger.info(f"delete the file {full_path}")
    os.unlink(full_path)


async def handle_create_file(reader, folder_path):
    full_path = await get_local_file_path(reader, folder_path.encode())
    content = await get_string(reader)
    assert not os.path.exists(full_path), f"{full_path} does exist"

    with open(full_path, "w") as file_to_write:
        file_to_write.write(content)


async def handle_modify_file(reader, folder_path):
    full_path = await get_local_file_path(reader, folder_path.encode())
    content = await get_string(reader)

    os.unlink(full_path)
    with open(full_path, "w") as file_to_write:
        file_to_write.write(content)


EDIT_TYPE_TO_HANDLER = {
    UserEditTypes.DELETE.value: handle_delete_file,
    UserEditTypes.CREATE.value: handle_create_file,
    UserEditTypes.MODIFY.value: handle_modify_file,
}


async def handle_user_edit(reader, writer, folder_path):
    logger.info("handle user edit request")
    data = reader.readexactly(UserEditMessage.EDIT_TYPE_LENGTH)
    edit_type = struct.unpack(">B", data)[0]
    logger.info(f"edit type is {edit_type}")

    try:
        await EDIT_TYPE_TO_HANDLER[edit_type](reader, folder_path)
        writer.write(UserEditResponse(StatusTypes.SUCCESS.value).pack())
        await writer.drain()
    except AssertionError:
        writer.write(UserEditResponse(StatusTypes.FAILURE.value).pack())
        await writer.drain()


async def handle_user_request(reader, writer, folder_path):
    logger.info("handle user request")

    full_path = await get_local_file_path(reader, folder_path.encode())
    expected_md5sum = await reader.readexactly(32)
    logger.info(f"local file path is {full_path}")
    with open(full_path, "r") as file_to_read:
        content = file_to_read.read()

    md5sum = calculate_md5(full_path)
    logger.info(f"md5sum of file is {md5sum}")
    assert expected_md5sum == md5sum.encode()
    writer.write(UserRequestResponse(os.path.relpath(full_path.decode(), folder_path), md5sum, content).pack())
    await writer.drain()
