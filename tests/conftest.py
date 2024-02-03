import pytest
import subprocess

import randomname

SERVER_PORT = 8080
SERVER_IP = "localhost"


@pytest.fixture(autouse=True)
def server(tmpdir_factory):
    new_dir = tmpdir_factory.mktemp("server-directory")
    server_process = subprocess.Popen(["python", "shared_folder_opu/server.py", new_dir.dirname],
                                      shell=True,
                                      stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)
    yield new_dir.dirname

    # TODO: make sure running
    server_process.kill()


@pytest.fixture()
def get_client(tmpdir_factory):
    clients = []

    def _get_client():
        new_dir = tmpdir_factory.mktemp(randomname.get_name())
        client_process = subprocess.Popen(["python", "shared_folder_opu/client.py", new_dir.dirname],
                                          shell=True,
                                          stdin=subprocess.PIPE,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE
                                          )
        clients.append(client_process)
        return new_dir.dirname

    yield _get_client

    for client in clients:
        client.kill()



