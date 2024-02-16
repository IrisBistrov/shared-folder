import os
import time


def test_create_file(server, get_client):
    client_folder1 = get_client()
    client_folder2 = get_client()
    new_file_name = "a"
    file_content = b"123"

    with open(os.path.join(client_folder1, new_file_name), "wb") as new_file:
        new_file.write(file_content)

    time.sleep(1)
    assert os.path.exists(os.path.join(client_folder2, new_file_name))
    with open(os.path.join(client_folder2, new_file_name)) as created_file:
        content_of_created = created_file.read()

    assert content_of_created.encode() == file_content
