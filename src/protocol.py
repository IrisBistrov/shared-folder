import struct
from enum import Enum
from operator import xor

from logger_singleton import SingletonLogger

logger = SingletonLogger.get_logger()

MESSAGE_TYPE_LENGTH = 1
MESSAGE_LENGTH_FIELD_LENGTH = 2
FILE_NAME_LENGTH_FIELD_LENGTH = 2


class MessageType(Enum):
    USER_EDIT = 0
    USER_REQUEST = 1
    SERVER_SYNC = 2
    SERVER_FILE = 3
    USER_EDIT_RESPONSE = 4


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
    DEFAULT_FORMAT = ">BBHsHs"
    DELETE_FORMAT = ">BBHs"

    def __init__(self, edit_type: UserEditTypes, file_name: bytes, content: bytes = None):
        logger.info(f"edit type is {edit_type.name} and content is {content}")
        assert xor(edit_type == UserEditTypes.MODIFY, content is None)
        self.edit_type = edit_type
        self.file_name = file_name
        self.content = content

    def pack(self):
        if self.edit_type.value is not UserEditTypes.MODIFY.value:
            return struct.pack(f">BBH{len(self.file_name)}s", self.CODE, self.edit_type.value, len(self.file_name),
                               self.file_name)

        return struct.pack(f">BBH{len(self.file_name)}sH{len(self.content)}s",
                           self.CODE,
                           self.edit_type.value,
                           len(self.file_name),
                           self.file_name,
                           len(self.content),
                           self.content)


class UserEditResponse:
    CODE = MessageType.USER_EDIT_RESPONSE.value

    def __init__(self, status: StatusTypes):
        self.status = status

    def pack(self):
        return struct.pack(">BB", self.CODE, self.status.value)


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

    def __init__(self, file_path: str, md5sum: str, content: str):
        self.file_path = file_path
        self.md5sum = md5sum
        self.content = content

    def pack(self):
        return struct.pack(f">BH{len(self.file_path)}sH{len(self.content)}s{len(self.md5sum)}s",
                           self.CODE,
                           len(self.file_path),
                           self.file_path.encode(),
                           len(self.content),
                           self.content.encode(),
                           self.md5sum.encode())


class ServerSyncMessage(Message):
    CODE = MessageType.SERVER_SYNC.value

    def __init__(self, data: bytes):
        self.data = data

    def pack(self):
        return struct.pack(f">BH{len(self.data)}s",
                           self.CODE,
                           len(self.data),
                           self.data)
