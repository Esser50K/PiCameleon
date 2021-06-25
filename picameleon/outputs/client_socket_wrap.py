class ClientSocketWrap:
    def __init__(self, client_socket, client_address, cleanup=None):
        self.cleanup = cleanup
        self.client_address = client_address
        self.client_socket = client_socket
        self.is_connected = True

    def close(self):
        if self.is_connected:
            self.client_socket.close()
            self.is_connected = False

        if self.cleanup is not None:
            self.cleanup(self.client_address)

    def write(self, data, timeout=5):
        try:
            if self.is_connected:
                self.client_socket.settimeout(timeout)
                self.client_socket.sendall(data)
        except Exception as e:
            print("Exception occurred when writing to client socket:", e)
            self.close()
            return False
        return True
