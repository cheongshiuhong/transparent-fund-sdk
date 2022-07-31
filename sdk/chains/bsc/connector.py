# Standard libraries
from typing import Any

# 3rd party libraries
from web3.middleware import geth_poa_middleware

# Code
from sdk.base.connector import BaseConnector


class BscConnector(BaseConnector):
    name = "Bsc Connector"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.connection.middleware_onion.inject(geth_poa_middleware, layer=0)
