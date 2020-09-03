import server
import client

def test_status_can_be_deserialized():
    client_ = client.Client(server.Server())
    client_.get_status()