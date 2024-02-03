import os
import struct
from asyncio import StreamReader, StreamWriter

from logger_singleton import SingletonLogger
from protocol import UserEditMessage, UserEditTypes, UserRequestResponse
from directory_utils import calculate_file_md5
from general_utils import get_string, get_local_file_path

logger = SingletonLogger.get_logger()


async def handle_delete_file(reader: StreamReader, folder_path: str):
    full_path = await get_local_file_path(reader, folder_path.encode())
    logger.info(f"handle deletion of file {full_path}")
    if not os.path.exists(full_path):
        logger.warning(f"file {full_path} does not exist")

    os.unlink(full_path)


async def handle_create_file(reader: StreamReader, folder_path: str):
    full_path = await get_local_file_path(reader, folder_path.encode())
    logger.info(f"handle creation of file {full_path}")
    if os.path.exists(full_path):
        logger.warning(f"{full_path} already exists, do nothing")
        return

    fd = os.open(full_path, os.O_CREAT)
    os.close(fd)


async def handle_modify_file(reader: StreamReader, folder_path: str):
    full_path = await get_local_file_path(reader, folder_path.encode())
    logger.info(f"handle modification of file {full_path}")
    content = await get_string(reader)

    os.unlink(full_path)
    with open(full_path, "w") as file_to_write:
        file_to_write.write(content.decode())


EDIT_TYPE_TO_HANDLER = {
    UserEditTypes.DELETE: handle_delete_file,
    UserEditTypes.CREATE: handle_create_file,
    UserEditTypes.MODIFY: handle_modify_file,
}


async def handle_user_edit(reader: StreamReader, folder_path: str):
    data = await reader.readexactly(UserEditMessage.EDIT_TYPE_LENGTH)
    edit_type = UserEditTypes(struct.unpack(">B", data)[0])
    await EDIT_TYPE_TO_HANDLER[edit_type](reader, folder_path)


async def handle_user_request(reader: StreamReader, writer: StreamWriter, folder_path: str):
    full_path = await get_local_file_path(reader, folder_path.encode())
    expected_md5sum = await reader.readexactly(32)
    logger.debug(f"user {writer} requested for {full_path}")

    with open(full_path, "r") as file_to_read:
        content = file_to_read.read()

    md5sum = calculate_file_md5(full_path)
    logger.debug(f"md5sum of {full_path} is {md5sum}")

    if expected_md5sum != md5sum.encode():
        logger.warning(f"expected md5sum is {expected_md5sum} but the updated value is {md5sum.encode()}")
        return

    writer.write(UserRequestResponse(os.path.relpath(full_path.decode(), folder_path), md5sum, content).pack())
    await writer.drain()
