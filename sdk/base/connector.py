# 3rd party libraries
from web3 import Web3


class BaseConnector:
    """
    The base connector class for handling the connection with EVM-based chains.
    """

    name: str
    connection: Web3

    def __init__(self, uri: str):
        self.connection = self.__load_connection(uri)

    @staticmethod
    def __load_connection(uri: str) -> Web3:
        """
        Gets the connection object given the endpoint to connect to.

        Args:
            uri: The endpoint to connect to.
        Returns:
            The connection object.
        """
        if not uri:
            raise ValueError("Endpoint cannot be empty.")

        if uri[:3] == "wss":
            return Web3(
                Web3.WebsocketProvider(uri, websocket_kwargs={"ping_interval": 10})
            )

        if uri[:4] == "http":
            return Web3(Web3.HTTPProvider(uri))

        # Raise exception if uri connection type is not supported
        raise NotImplementedError("Endpoint connection type not supported.")

    def is_connected(self) -> bool:
        return self.connection.isConnected()
