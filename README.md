# shared-folder

a pythonic package for sharing a folder on linux. Was developed on ubuntu 22.04.1. 

## Installation

to run the unit tests you should install the package, run the following
command from the main folder of the project. 

```commandline
sudo -H pip3 install -e .
```

## Tests

after you installed the package, run from the same folder:

```commandline
python3 -m pytest
```

## Usage

to run the server: 

```commandline
python3 server_main.py /tmp/server/
```

in this case the folder that will be shared is `/tmp/server`.

to run the client:

```commandline
python3 client_main.py /tmp/client/
```

the folder that will be synced with the server is `/tmp/client`.

Now you are able to edit the contents of the folder and the server and client will be 
synchronized. Please note that you should not edit the shared folder on the server, 
only on the client. 

to change the server host and port you should change the file `configuration.py`.
the format is: 

```python
SERVER_HOST = "localhost"
SERVER_PORT = 8080
```

