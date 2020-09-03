import pytest

import client


def test_rejects_invalid_server_early():
    with pytest.raises(ValueError):
        client.Client(None)
