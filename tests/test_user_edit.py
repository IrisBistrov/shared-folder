import os
import time
import logging

logger = logging.getLogger(__name__)


def test_new_file(server, get_client):
    client_folder = get_client()
    new_file_name = "a"
    file_content = b"123"
    logger.info(f"client folder {client_folder} and server folder is {server}")

    with open(os.path.join(client_folder, new_file_name), "wb") as new_file:
        new_file.write(file_content)

    time.sleep(1)
    assert os.path.exists(os.path.join(server, new_file_name))
    with open(os.path.join(server, new_file_name)) as created_file:
        content_of_created = created_file.read()

    assert content_of_created.encode() == file_content


def test_create_dir(server, get_client):
    client_folder = get_client()
    new_dir_name = "1"

    os.mkdir(os.path.join(client_folder, new_dir_name))
    time.sleep(1)
    assert os.path.exists(os.path.join(server, new_dir_name))
