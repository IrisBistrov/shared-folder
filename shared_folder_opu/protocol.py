import struct
from enum import Enum
from operator import xor

from shared_folder_opu.logger_singleton import SingletonLogger

logger = SingletonLogger.get_logger()

MESSAGE_TYPE_LENGTH = 1
MESSAGE_LENGTH_FIELD_LENGTH = 2
FILE_NAME_LENGTH_FIELD_LENGTH = 2


class MessageType(Enum):
    USER_EDIT = 0
    USER_REQUEST = 1
    SERVER_SYNC = 2
    SERVER_FILE = 3


class UserEditTypes(Enum):
    CREATE = 0
    DELETE = 1
    MODIFY = 2


class StatusTypes(Enum):
    FAILURE = 0
    SUCCESS = 1


class Message:
    def pack(self):
        raise NotImplemented


class UserEditMessage(Message):
    EDIT_TYPE_LENGTH = 1
    CODE = MessageType.USER_EDIT.value

    def __init__(self, edit_type: UserEditTypes, file_name: bytes, content: bytes = None, is_dir=None):
        logger.info(f"edit type is {edit_type.name} and content is {content}")
        assert xor(edit_type == UserEditTypes.MODIFY, content is None)
        self.edit_type = UserEditTypes(edit_type)
        self.file_name = file_name
        self.content = content
        self.is_dir = is_dir

    def pack(self) -> bytes:
        match self.edit_type:
            case UserEditTypes.DELETE:
                return struct.pack(f">BBH{len(self.file_name)}s",
                                   self.CODE, self.edit_type.value,
                                   len(self.file_name),
                                   self.file_name)

            case UserEditTypes.MODIFY:
                return struct.pack(f">BBH{len(self.file_name)}sH{len(self.content)}s",
                                   self.CODE,
                                   self.edit_type.value,
                                   len(self.file_name),
                                   self.file_name,
                                   len(self.content),
                                   self.content)

            case UserEditTypes.CREATE:
                return struct.pack(f">BBH{len(self.file_name)}sB",
                                   self.CODE, self.edit_type.value,
                                   len(self.file_name),
                                   self.file_name,
                                   self.is_dir)

            case _:
                raise RuntimeError(f"Attempted to pack an invalid message of type {self.edit_type.name}")


class UserRequestMessage(Message):
    CODE = MessageType.USER_REQUEST.value

    def __init__(self, file_path: str, md5sum: str):
        self.file_path = file_path
        self.md5sum = md5sum

    def pack(self):
        return struct.pack(f">BH{len(self.file_path)}s{len(self.md5sum)}s",
                           self.CODE,
                           len(self.file_path),
                           self.file_path.encode(),
                           self.md5sum.encode())


class UserRequestResponse(Message):
    CODE = MessageType.SERVER_FILE.value

    def __init__(self, file_path: str, content: str):
        self.file_path = file_path
        self.content = content

    def pack(self):
        return struct.pack(f">BH{len(self.file_path)}sH{len(self.content)}s",
                           self.CODE,
                           len(self.file_path),
                           self.file_path.encode(),
                           len(self.content),
                           self.content.encode())


class ServerSyncMessage(Message):
    CODE = MessageType.SERVER_SYNC.value

    def __init__(self, data: bytes):
        self.data = data

    def pack(self):
        return struct.pack(f">BH{len(self.data)}s",
                           self.CODE,
                           len(self.data),
                           self.data)
