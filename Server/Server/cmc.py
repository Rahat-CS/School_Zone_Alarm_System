"""CMC Multiplexer

Allows ADCs to connect on one TCP port, Individual CMC processes connect on another.


Based on code from:
https://github.com/python/asyncio/blob/master/examples/simple_tcp_server.py


# Usage

## COMMANDS

### TRIG

Send a UDP message to the ADC to trigger it to connect to the CMC

### DIS

Disconnect the CMC's TCP/IP connection to the ADC

### PING

Send a single ICMP ping packet to the ADC's address and wait for a response.

### STAT

Get the status of the ADC connection

All other lines are sent to the ADC's via the TCP connection.

(c) DEK Technologies 2022

"""

import asyncio
import asyncio.streams
import collections
import socket
import subprocess

import logging

logger = logging.getLogger(__name__)

# Used for both connections from ADCs and from Management Controllers
Connection = collections.namedtuple('Connection', 'reader writer task')

async def quick_ping(dest_ip_addr):
    proc = await asyncio.create_subprocess_shell(
        f'ping -c 1 -w 5 {dest_ip_addr}',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    print(f'ping exited with {proc.returncode}]')
    if stdout:
        print(f'[stdout]\n{stdout.decode()}')
    if stderr:
        print(f'[stderr]\n{stderr.decode()}')

    if proc.returncode == 0:
        return True
    if proc.returncode == 1:
        return False
    raise Exception(proc.returncode, proc)


class AdcTrigger:
    """
    One AdcTrigger instance server for all ADCs.
    """
    def __init__(self, cmc_host, cmc_udp_port, adc_udp_port):
        self.adc_udp_port = adc_udp_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((cmc_host, cmc_udp_port))

    def send(self, adc_ip_addr):
        """Send a UDP trigger to an ADC.

        """
        self.socket.sendto(b' ', (adc_ip_addr, self.adc_udp_port))
        logger.debug(f"trigger sent to {adc_ip_addr}")


class AdcLink:
    """
    Handles the connection between a particular ADC and its MC
    """

    def __init__(self, adc_ip_addr, trigger):
        self.adc_ip_addr = adc_ip_addr
        self.mc = None
        self.adc = None
        self.incoming = b''
        self.trigger = trigger
        self.history = []


    async def mc_report(self, message):
        """
        Send information about the link to the MC.

        These are prefixed with "!!!" to allow them to be differentiated from CMC traffic.
        """
        await self.mc.writer.drain()
        self.mc.writer.write(f"!!!{message}\n".encode())

    def _adc_client_done(self, task):
        """
        The ADC has disconnected
        """
        if self.adc is None or task != self.adc.task:
            logger.warning(f"Unexpected ADC {self.adc_ip_addr} closed")

        if self.incoming:
            logger.warning(f"ADC {self.adc_ip_addr} closed mid message ({self.incoming})")
            self.incoming = b''
        logger.debug(f"ADC {self.adc_ip_addr}: client task done")
        self.adc = None
        if self.mc:
            self.mc.writer.write(b"!!!ADC disconnects\n")

    def adc_connect(self, client_reader, client_writer):
        if self.adc is not None:
            logger.warning(f"duplicate ADC for {self.adc_ip_addr} '{self.incoming}'")
            self.incoming = b''
            if self.mc:
                self.mc.writer.write(b"!!!duplicate ADC accepted\n")
        task = asyncio.Task(self.handle_adc())
        self.adc = Connection(client_reader, client_writer, task)
        logger.info(f"new ADC {self.adc_ip_addr}")
        if self.mc:
            self.mc.writer.write(b"!!!ADC connects\n")
        task.add_done_callback(self._adc_client_done)

    def _mc_client_done(self, task):
        if self.mc is None or task != self.mc.task:
            logger.warning(f"Unexpected MC for {self.adc_ip_addr} closed")
        logger.debug(f"MC for {self.adc_ip_addr}: client task done")
        self.mc = None

    def mc_register(self, client_reader, client_writer):
        if self.mc is not None:
            logger.warning(f"duplicate MC for {self.adc_ip_addr}")
            client_writer.write(b"!!!you are a duplicate MC\n")

            self.mc.writer.write(b"!!!duplicate MC accepted\n")
        task = asyncio.current_task()
        self.mc = Connection(client_reader, client_writer, task)
        if self.adc:
            self.mc.writer.write(b"!!!ADC already connected\n")
        else:
            self.mc.writer.write(b"!!!ADC not yet connected\n")
        logger.debug(f"register MC for {self.adc_ip_addr}")
        task.add_done_callback(self._mc_client_done)

        return False

    async def _disconnect_adc(self):
        """
        The MC has signalled it wants the ADC link terminated
        """
        if self.adc:
            logger.debug(f"disconnecting from ADC {self.adc_ip_addr}")
            self.adc.writer.write_eof()
            self.adc.writer.close()
            await self.adc.writer.wait_closed()
            logger.info(f"ADC {self.adc_ip_addr} disconnected")
        else:
            logger.info(f"No ADC {self.adc_ip_addr} connection active")


    async def process_mc_input(self, line):
        """A line of input has arrived from the management controller

        Either interpret it locally or pass it through to the corresponding ADC.
        """
        if line == b'':
            # The MC session has ended.  Terminate the ADC session in turn.
            logger.info(f"MC for {self.adc_ip_addr} disconnects")
            await self._disconnect_adc()
            return True

        sline = line.strip()

        if sline == b'TRIG':
            logger.info(f"UDP trigger to {self.adc_ip_addr}")
            self.trigger.send(self.adc_ip_addr)
            await self.mc_report("UDP trigger sent")

        elif sline == b'DIS':
            logger.info(f"Disconnect {self.adc_ip_addr}")
            await self._disconnect_adc()

        elif sline == b'STAT':
            if self.adc:
                if self.adc.reader.at_eof():
                    logger.info(f"ADC {self.adc_ip_addr} at EOF")
                    state = "DOWN"
                else:
                    state = "UP"
            else:
                state = "DOWN"
            logger.info(f"ADC {self.adc_ip_addr} state reported as {state}")
            await self.mc_report(f"ADC link is {state}")

        elif sline == b'PING':
            can_ping = await quick_ping(self.adc_ip_addr)
            await self.mc_report(f"ADC link is {can_ping}")

        elif sline == b'INFO':
            logger.info(f"Info {self.adc_ip_addr}")

            await self.mc_report(f"INFO")

        else:
            if self.adc is None:
                logger.warning(f"{self.adc_ip_addr} is not connected")
                await self.mc_report("not connected to ADC")
            else:
                logger.debug(f"Send {sline} to {self.adc_ip_addr}")
                self.adc.writer.write(sline)
                await self.adc.writer.drain()
        return False

    async def handle_adc(self):
        """
        We have got incoming traffic from the CMC connection

        Accumulate it up until there is a terminating ">" character and then
        relay it to the MC.
        """
        logger.debug('handle_adc')
        self.incoming = b''
        while True:
            try:
                 incoming = await self.adc.reader.read(1)
            except ConnectionResetError as e:
                logger.info(f"ADC {self.adc_ip_addr} resets the connection i={self.incoming}")
                break
            except Exception as e:
                logger.error(f"{self.adc_ip_addr} read error: {e} type={type(e)} i={self.incoming}")
                break
            if not incoming:
                logger.info(f"ADC {self.adc_ip_addr} disconnects i={self.incoming}")
                break
            self.incoming += incoming
            if incoming == b'>':
                if self.mc is None:
                    logger.info(f"MCless ADC {self.adc_ip_addr} sends {self.incoming}")
                else:
                    logger.debug(f"ADC {self.adc_ip_addr} sends {self.incoming}")
                    self.mc.writer.write(self.incoming + b'\n')
                    await self.mc.writer.drain()
                self.incoming =b''


class CmcServer:
    """
    """

    def __init__(self, args):
        self.adc_links = {}
        self.adc_server = None # encapsulates the server sockets
        self.mc_server = None # encapsulates the server sockets
        self.args = args

        # use same port number on CMC for TCP and UDP
        self.trigger = AdcTrigger(args.cmc_host, args.cmc_port, args.adc_udp_port)



    def _accept_adc_client(self, client_reader, client_writer):
        """
        This method accepts a new ADC connection.

        If the corresponding MC is already registered then notify it.
        """

        adc_ip_addr = client_writer.get_extra_info('peername')[0]

        if adc_ip_addr not in self.adc_links:
            self.adc_links[adc_ip_addr] = AdcLink(adc_ip_addr, self.trigger)
        else:
            logger.info(f"ADC {adc_ip_addr} connects to existing link")

        link = self.adc_links[adc_ip_addr]

        link.adc_connect(client_reader, client_writer)


    def _accept_mc_client(self, client_reader, client_writer):
        """
        This method accepts a new Management Controller connection.
        """

        # start a new Task to handle this specific client connection
        task = asyncio.Task(self._handle_mc_client(client_reader, client_writer))

        logger.info(f"new MC at {client_writer.get_extra_info('peername')[0]}")


    async def _handle_mc_client(self, client_reader, client_writer):
        """
        Started exclusively by _accept_mc_client()
        """

        # The first thing the MC sends is the IP address of the ADC it is
        # connecting to.
        data = await client_reader.readline()
        adc_ip_addr = data.decode("utf-8").strip()
        logger.info(f'MC for {adc_ip_addr} connecting')

        if adc_ip_addr not in self.adc_links:
            self.adc_links[adc_ip_addr] = AdcLink(adc_ip_addr, self.trigger)
        else:
            logger.info(f"link for ADC {adc_ip_addr} already established")

        link = self.adc_links[adc_ip_addr]
        halt = link.mc_register(client_reader, client_writer)

        if halt:
            client_writer.close()
            return

        while not halt:
            # logger.debug(f"waiting for MC input...")
            line = await client_reader.readline()
            halt = await link.process_mc_input(line)

        await client_writer.drain()



    def start(self, loop):
        """
        Starts the TCP services, one listening for ADC connections, one for MC connections.

        For each client that connects, the accept_client method gets
        called.  This method runs the loop until the server sockets
        are ready to accept connections.
        """
        self.adc_server = loop.run_until_complete(
            asyncio.streams.start_server(
                self._accept_adc_client,
                self.args.cmc_host, self.args.cmc_port,
                loop=loop
            )
        )

        self.mc_server = loop.run_until_complete(
            asyncio.streams.start_server(
                self._accept_mc_client,
                self.args.mc_host,  self.args.mc_port,
                loop=loop
            )
        )

    def stop(self, loop):
        """
        Stops the TCP server, i.e. closes the listening socket(s).

        This method runs the loop until the server sockets are closed.
        """
        for server, name in [(self.adc_server, 'ADC'), (self.mc_server, 'MC')]:
            if server is not None:
                logger.info(f"Stopping {name} server")
                server.close()
                loop.run_until_complete(server.wait_closed())
                logger.info(f"{name} server stopped")
                server = None


def main(args):

    loop = asyncio.get_event_loop()

    # creates a server and starts listening to TCP connections
    server = CmcServer(args)
    server.start(loop)
    logger.info("Started")
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info(f"KeyboardInterrupt")
        server.stop(loop)
        logger.info(f"Stopped")


if __name__ == '__main__':

    import argparse
    from dek import dekalog

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--cmc-port", type=int, default=8006,
        help="Port for ADCs to connect to. Default=%(default)s"
    )
    parser.add_argument(
        "--cmc-host", type=str, default='',
        help="IP address that ADCs connect to. Default is ANY"
    )
    parser.add_argument(
        "--mc-port", type=int, default=8806,
        help="Port for Management Controller to connect to. Default=%(default)s"
    )
    parser.add_argument(
        "--mc-host", type=str, default='',
        help="IP address that Management Controllers connect to. Default is ANY"
    )

    parser.add_argument(
        "--adc-udp-port", type=int, default=10080,
        help="Port the ADC listens on for triggers from the CMC. Default=%(default)s"
    )

    dekalog.add_logging_args(parser)

    args = parser.parse_args()

    dekalog.set_up_logging(args)

    main(args)
