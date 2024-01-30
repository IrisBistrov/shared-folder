import os
import struct
from asyncio import StreamReader, StreamWriter

from logger_singleton import SingletonLogger
from protocol import UserEditMessage, UserEditTypes, UserRequestResponse, StatusTypes, \
    UserEditResponse
from directory_utils import calculate_md5
from general_utils import get_string, get_local_file_path

logger = SingletonLogger.get_logger()


async def handle_delete_file(reader: StreamReader, folder_path: str):
    logger.info("handle delete file")
    full_path = await get_local_file_path(reader, folder_path.encode())
    logger.info(f"the full path of the deleted file is {full_path}")
    assert os.path.exists(full_path), f"{full_path} does not exist"
    logger.info(f"delete the file {full_path}")
    os.unlink(full_path)


async def handle_create_file(reader: StreamReader, folder_path: str):
    logger.info("handle create file")
    full_path = await get_local_file_path(reader, folder_path.encode())
    logger.info(f"the created file full path is {full_path}")
    assert not os.path.exists(full_path), f"{full_path} does exist"
    fd = os.open(full_path, os.O_CREAT)
    os.close(fd)


async def handle_modify_file(reader: StreamReader, folder_path: str):
    logger.info("handle modify file")
    full_path = await get_local_file_path(reader, folder_path.encode())
    logger.info(f"the full path of the modified file is {full_path}")
    content = await get_string(reader)
    logger.info("got the content of the modified file")

    os.unlink(full_path)
    with open(full_path, "w") as file_to_write:
        file_to_write.write(content.decode())


EDIT_TYPE_TO_HANDLER = {
    UserEditTypes.DELETE: handle_delete_file,
    UserEditTypes.CREATE: handle_create_file,
    UserEditTypes.MODIFY: handle_modify_file,
}


async def handle_user_edit(reader: StreamReader, writer: StreamWriter, folder_path: str):
    logger.info("handle user edit request")
    data = await reader.readexactly(UserEditMessage.EDIT_TYPE_LENGTH)
    edit_type = UserEditTypes(struct.unpack(">B", data)[0])
    logger.info(f"edit type is {edit_type}")

    try:
        await EDIT_TYPE_TO_HANDLER[edit_type](reader, folder_path)
        writer.write(UserEditResponse(StatusTypes.SUCCESS).pack())
        await writer.drain()
    except AssertionError:
        writer.write(UserEditResponse(StatusTypes.FAILURE).pack())
        await writer.drain()


async def handle_user_request(reader: StreamReader, writer: StreamWriter, folder_path: str):
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
