from raft import __version__


def test_version():
    assert __version__ == '0.1.0'

def test_ping():
    from raft.node import Node

    node_instance = Node('locahost',8000)
    node_instance.send_msg()