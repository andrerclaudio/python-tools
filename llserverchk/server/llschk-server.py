#!/usr/bin/env python3
# pylint: disable=line-too-long
# indent = tab
# tab-size = 4

"""
Copyright (c) 2023 Andre Ribeiro Claudio
Author: Andre Ribeiro

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

# Build-in libraries
import logging
import time
import socket

# Initialize logging here
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Script starting point.

    UDP_IP_ADDRESS = "127.0.0.1"
    UDP_PORT_NO = 6789

    try:
        serverSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        serverSock.bind((UDP_IP_ADDRESS, UDP_PORT_NO))
        logger.info(f"UDP server started on {UDP_IP_ADDRESS}:{UDP_PORT_NO}")

        while True:
            try:
                data, addr = serverSock.recvfrom(1024)
                logger.info(f"Received message from {addr}: {data.decode()}")
            except Exception as e:
                logger.error(f"Error receiving message: {str(e)}")

    except KeyboardInterrupt:
        logger.info('Server stopped by the user.')
    except socket.error as e:
        logger.error(f"Failed to start UDP server: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
    finally:
        serverSock.close()
        logger.info("UDP server stopped")
