import struct
from enum import Enum

from logger_singleton import SingletonLogger

logger = SingletonLogger.get_logger()

MESSAGE_TYPE_LENGTH = 1
MESSAGE_LENGTH_FIELD_LENGTH = 2


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
    pass


class UserEditMessage(Message):
    CODE = MessageType.USER_EDIT.value
    DEFAULT_FORMAT = ">BBHHss"
    DELETE_FORMAT = ">BBHs"

    def __init__(self, edit_type, file_name, content=None):
        assert edit_type in MessageType
        self.edit_type = edit_type
        self.file_name = file_name
        self.content = content

    def pack(self):
        if self.edit_type is UserEditTypes.DELETE:
            return struct.pack(f">BBH{len(self.file_name)}s", self.CODE, self.edit_type, len(self.file_name), self.file_name)

        return struct.pack(f">BBHH{len(self.file_name)}s{len(self.content)}s",
                           self.CODE,
                           self.edit_type,
                           len(self.file_name),
                           len(self.content),
                           self.file_name,
                           self.content)


class UserEditResponse:
    CODE = MessageType.USER_EDIT_RESPONSE.value

    def __init__(self, status):
        assert status in StatusTypes
        self.status = status

    def pack(self):
        return struct.pack(">BB", self.CODE, self.status)


class UserRequestMessage(Message):
    CODE = MessageType.USER_REQUEST.value

    def __init__(self, file_path, md5sum):
        self.file_path = file_path
        self.md5sum = md5sum

    def pack(self):
        return struct.pack(f">BH{len(self.md5sum)}s{len(self.file_path)}s", self.CODE, len(self.file_path), self.md5sum, self.file_path)


class UserRequestResponse(Message):
    CODE = MessageType.SERVER_FILE.value

    def __init__(self, file_path, md5sum, content):
        self.file_path = file_path
        self.md5sum = md5sum
        self.content = content

    def pack(self):
        return struct.pack(f">BHH{len(self.md5sum)}s{len(self.file_path)}s{len(self.content)}s",
                           self.CODE,
                           len(self.file_path),
                           len(self.content),
                           self.md5sum,
                           self.file_path,
                           self.content)


class ServerSyncMessage(Message):
    CODE = MessageType.SERVER_SYNC.value

    def __init__(self, data):
        self.data = data

    def pack(self):
        return struct.pack(f">BH{len(self.data)}s", self.CODE, len(self.data), self.data)
