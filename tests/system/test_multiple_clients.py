import os
import time

import pytest
import randomname


@pytest.mark.parametrize("number_of_clients", [2, 5])
def test_create_file_on_one_client(server_folder, get_client, number_of_clients: int):
    clients = []

    for _ in range(number_of_clients):
        clients.append(get_client())
    new_file_name = "a"
    file_content = b"123"

    with open(os.path.join(clients[0], new_file_name), "wb") as new_file:
        new_file.write(file_content)

    time.sleep(1)
    for client_folder in clients[1:]:
        assert os.path.exists(os.path.join(client_folder, new_file_name))
        with open(os.path.join(client_folder, new_file_name)) as created_file:
            content_of_created = created_file.read()

        assert content_of_created.encode() == file_content


@pytest.mark.parametrize("number_of_clients", [2, 5])
def test_all_clients_sync_with_server_file(server_folder, get_client, number_of_clients: int):
    file_name, content = "file", "I Love Computer Networks"
    with open(os.path.join(server_folder, file_name), "w") as my_file:
        my_file.write(content)
    clients = []

    for _ in range(number_of_clients):
        clients.append(get_client())

    time.sleep(1)
    for client_folder in clients:
        assert os.path.exists(os.path.join(client_folder, file_name)), "file does not exist"
        with open(os.path.join(client_folder, file_name)) as created_file:
            content_of_created = created_file.read()

        assert content_of_created == content, "the content of the file is not right"


@pytest.mark.parametrize("number_of_clients", [2, 5])
def test_all_clients_sync_with_server_dir(server_folder, get_client, number_of_clients: int):
    directory_name = randomname.get_name()
    os.mkdir(os.path.join(server_folder, directory_name))
    clients = []

    for _ in range(number_of_clients):
        clients.append(get_client())

    time.sleep(1)
    for client_folder in clients:
        assert os.path.exists(os.path.join(client_folder, directory_name))
        assert os.path.isdir(os.path.join(client_folder, directory_name))

