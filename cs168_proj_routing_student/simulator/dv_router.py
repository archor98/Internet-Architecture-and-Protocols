"""
Your awesome Distance Vector router for CS 168

Based on skeleton code by:
  MurphyMc, zhangwen0411, lab352
"""

import sim.api as api
from cs168.dv import RoutePacket, \
                     Table, TableEntry, \
                     DVRouterBase, Ports, \
                     FOREVER, INFINITY

class DVRouter(DVRouterBase):

    # A route should time out after this interval
    ROUTE_TTL = 15

    # Dead entries should time out after this interval
    GARBAGE_TTL = 10

    # -----------------------------------------------
    # At most one of these should ever be on at once
    SPLIT_HORIZON = False
    POISON_REVERSE = False
    # -----------------------------------------------
    
    # Determines if you send poison for expired routes
    POISON_EXPIRED = False

    # Determines if you send updates when a link comes up
    SEND_ON_LINK_UP = False

    # Determines if you send poison when a link goes down
    POISON_ON_LINK_DOWN = False

    def __init__(self):
        """
        Called when the instance is initialized.
        DO NOT remove any existing code from this method.
        However, feel free to add to it for memory purposes in the final stage!
        """
        assert not (self.SPLIT_HORIZON and self.POISON_REVERSE), \
                    "Split horizon and poison reverse can't both be on"
        
        self.start_timer()  # Starts signaling the timer at correct rate.

        # Contains all current ports and their latencies.
        # See the write-up for documentation.
        self.ports = Ports()
        
        # This is the table that contains all current routes
        self.table = Table()
        self.table.owner = self
        self.past = {}


    def add_static_route(self, host, port):
        """
        Adds a static route to this router's table.

        Called automatically by the framework whenever a host is connected
        to this router.

        :param host: the host.
        :param port: the port that the host is attached to.
        :returns: nothing.
        """
        # `port` should have been added to `peer_tables` by `handle_link_up`
        # when the link came up.
        assert port in self.ports.get_all_ports(), "Link should be up, but is not."

        # TODO: fill this in!
        self.table[host] = TableEntry(host, port, self.ports.get_latency(port),FOREVER)

    def handle_data_packet(self, packet, in_port):
        """
        Called when a data packet arrives at this router.

        You may want to forward the packet, drop the packet, etc. here.

        :param packet: the packet that arrived.
        :param in_port: the port from which the packet arrived.
        :return: nothing.
        """
        # TODO: fill this in!
        for keys in self.table.keys():
            if keys == packet.dst:
                tableEntry = self.table[packet.dst]
                if tableEntry == None:
                    return
                dist = tableEntry[1]
                exit = tableEntry[2]
                if exit >= INFINITY:
                    return
                self.send(packet, dist)
                return

    def send_routes(self, force=False, single_port=None):
        """
        Send route advertisements for all routes in the table.

        :param force: if True, advertises ALL routes in the table;
                      otherwise, advertises only those routes that have
                      changed since the last advertisement.
               single_port: if not None, sends updates only to that port; to
                            be used in conjunction with handle_link_up.
        :return: nothing.
        """
        # TODO: fill this in!
        for port in self.ports.get_all_ports():
            for destination in self.table.keys():
                self.helper1(force, port, destination)

    def expire_routes(self):
        """
        Clears out expired routes from table.
        accordingly.
        """
        # TODO: fill this in!
        for destination in list(self.table):
            time_measure = self.table[destination][3]
            lat = self.table[destination][2]
            bol3 = self.POISON_EXPIRED
            bol2 = lat < INFINITY
            bol1 = (time_measure < api.current_time())
            if bol1 and bol3 and bol2:
                self.table[destination] = TableEntry(destination, self.table[destination][1], INFINITY, api.current_time() + self.ROUTE_TTL)
            if bol1 and (not bol3 or not bol2):
                    del self.table[destination]

    def handle_route_advertisement(self, route_dst, route_latency, port):
        """
        Called when the router receives a route advertisement from a neighbor.
        :param route_dst: the destination of the advertised route.
        :param route_latency: latency from the neighbor to the destination.
        :param port: the port that the advertisement arrived on.
        :return: nothing.
        """
        # TODO: fill this in!
        portlat = self.ports.get_latency(port)
        curlat = INFINITY
        curport = -100000
        if (route_dst in self.table.keys()):
            curport = self.table[route_dst][1]
            curlat = self.table[route_dst][2]
            if (curport == port or curlat > route_latency + portlat):
                if (curport == port and route_latency >= INFINITY and curlat >= INFINITY) or (route_latency >= INFINITY and curport != port):
                    return
                else:
                    new_portlat = min(route_latency + portlat, INFINITY)
                    time = api.current_time() + self.ROUTE_TTL
                    self.table[route_dst] = TableEntry(route_dst, port, new_portlat, time)
                    self.send_routes(False)
                    if (route_dst, port) in self.past and curport != port and curlat < INFINITY <= route_latency:
                        del self.past[(route_dst, port)]
        else:
            if (curport == port or curlat > route_latency + portlat):
                if (curport == port and route_latency >= INFINITY and curlat >= INFINITY) or (route_latency >= INFINITY and curport != port):
                    return
                else:
                    new_portlat = min(route_latency + portlat, INFINITY)
                    time = api.current_time() + self.ROUTE_TTL
                    self.table[route_dst] = TableEntry(route_dst, port, new_portlat, time)
                    self.send_routes(False)
                    if (route_dst, port) in self.past and curport != port and curlat < INFINITY <= route_latency:
                        del self.past[(route_dst, port)]
            



    def handle_link_up(self, port, latency):
        """
        Called by the framework when a link attached to this router goes up.
        :param port: the port that the link is attached to.
        :param latency: the link latency.
        :returns: nothing.
        """
        self.ports.add_port(port, latency)

        # TODO: fill in the rest!

    def handle_link_down(self, port):
        """
        Called by the framework when a link attached to this router does down.
        :param port: the port number used by the link.
        :returns: nothing.
        """
        self.ports.remove_port(port)

        # TODO: fill this in!
        if(self.POISON_ON_LINK_DOWN == True):
            for destination in self.table.keys():
                time = api.current_time() + self.ROUTE_TTL
                if self.table[destination][1] == port:
                    self.table[destination] = TableEntry(destination, port, INFINITY, time)
            self.send_routes(False)
        else:
            return 
        

        

    # Feel free to add any helper methods!
    def helper1(self, force, port, destination):
        curlat = self.table[destination][2]
        bol1 = (self.SPLIT_HORIZON == False)
        bol2 = (self.table[destination][1] != port)
        bol3 = (self.POISON_REVERSE == True)
        bol4 = (self.table[destination][1] == port)
        def helper2(destination, lat, port):
            self.send(RoutePacket(destination, lat), port)
            self.past[(destination, port)] = lat
        if ((bol1 or bol2)):
            if (bol3 and bol4):
                if (force == True):
                    helper2(destination,INFINITY, port)
                else:
                    if ((destination,port) not in self.past.keys() or self.past[(destination, port)] != INFINITY):
                        helper2(destination,INFINITY, port)
            else:
                if (force == True):
                    helper2(destination,curlat, port)
                else:
                    if (destination, port) not in self.past.keys() or (self.past[(destination, port)] != curlat):
                        self.send(RoutePacket(destination, curlat), port)
                    self.past[(destination,port)] = curlat


                        

