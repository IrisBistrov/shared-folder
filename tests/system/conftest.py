import pytest
import subprocess

import randomname

SERVER_PORT = 8080
SERVER_IP = "localhost"


@pytest.fixture(autouse=True)
def server_folder(tmpdir_factory):
    new_dir = tmpdir_factory.mktemp("server-directory")
    server_process = subprocess.Popen(["python", "server_main.py", new_dir.dirname],
                                      shell=True,
                                      stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)
    yield new_dir.dirname

    assert server_process.poll() is None
    server_process.kill()


@pytest.fixture()
def get_client(tmpdir_factory):
    clients = []

    def _get_client():
        new_dir = tmpdir_factory.mktemp(randomname.get_name())
        client_process = subprocess.Popen(["python", "client_main.py", new_dir.dirname],
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
