import simpy
import random
from simulator.log import logger
from entities.packet import DataPacket, AckPacket, RreqPacket, RrepPacket, RerrPacket
from utils import config

class Aodv:
    """
    Ad hoc On-Demand Distance Vector (AODV) Routing Protocol
    """
    def __init__(self, simulator, my_drone):
        self.simulator = simulator
        self.my_drone = my_drone
        self.env = simulator.env
        
        # Routing table: dest_id -> {next_hop, hop_count, seq_num, expiry_time}
        self.routing_table = {}
        
        # Buffer for packets waiting for route: dest_id -> [packets]
        self.packet_buffer = {}
        
        # RREQ ID counter
        self.rreq_id = 0
        
        # Sequence number
        self.seq_num = 0
        
        # Seen RREQs: (src_id, broadcast_id) -> expiry_time
        self.seen_rreqs = {}
        
        # Constants
        self.ACTIVE_ROUTE_TIMEOUT = 3.0 * 1e6  # 3 seconds
        self.NET_DIAMETER = 35
        self.NODE_TRAVERSAL_TIME = 40000 # 40ms
        self.NET_TRAVERSAL_TIME = 2 * self.NODE_TRAVERSAL_TIME * self.NET_DIAMETER
        self.PATH_DISCOVERY_TIME = 2 * self.NET_TRAVERSAL_TIME
        
        self.env.process(self.purge_routes())

    def next_hop_selection(self, packet):
        """
        Select next hop for data packet.
        If no route, initiate RREQ and buffer packet.
        """
        dest_id = packet.dst_drone.identifier
        current_time = self.env.now
        
        # Check if route exists and is valid
        if dest_id in self.routing_table:
            entry = self.routing_table[dest_id]
            if entry['expiry_time'] > current_time:
                packet.next_hop_id = entry['next_hop']
                # Update expiry on usage
                entry['expiry_time'] = current_time + self.ACTIVE_ROUTE_TIMEOUT
                return True, packet, True # has_route, packet, enquire
            else:
                del self.routing_table[dest_id]
        
        # No route, buffer packet and send RREQ
        if dest_id not in self.packet_buffer:
            self.packet_buffer[dest_id] = []
            self.send_rreq(dest_id)
            
        self.packet_buffer[dest_id].append(packet)
        return False, packet, False

    def send_rreq(self, dest_id):
        self.rreq_id += 1
        self.seq_num += 1
        
        # Determine dest_seq (use last known if available)
        dest_seq = 0
        if dest_id in self.routing_table:
            dest_seq = self.routing_table[dest_id]['seq_num']
            
        config.GL_ID_HELLO_PACKET += 1 # Use generic ID counter for control packets
        channel_id = self.my_drone.channel_assigner.channel_assign()
        
        rreq = RreqPacket(src_drone=self.my_drone,
                          creation_time=self.env.now,
                          packet_id=config.GL_ID_HELLO_PACKET, # Reuse ID space
                          packet_length=config.HELLO_PACKET_LENGTH, # Approx size
                          simulator=self.simulator,
                          channel_id=channel_id,
                          broadcast_id=self.rreq_id,
                          dest_id=dest_id,
                          dest_seq=dest_seq,
                          src_seq=self.seq_num,
                          hop_count=0)
        
        logger.info(f"At time: {self.env.now} (us) ---- UAV: {self.my_drone.identifier} sends RREQ for Dest: {dest_id}")
        self.my_drone.transmitting_queue.put(rreq)
        
        # Record RREQ to avoid reprocessing my own
        self.seen_rreqs[(self.my_drone.identifier, self.rreq_id)] = self.env.now + self.PATH_DISCOVERY_TIME

    def packet_reception(self, packet, sender_id):
        """Handle incoming packets"""
        current_time = self.env.now
        
        if isinstance(packet, RreqPacket):
            self.handle_rreq(packet, sender_id)
            yield self.env.timeout(0)  # Must yield for simpy process
        elif isinstance(packet, RrepPacket):
            self.handle_rrep(packet, sender_id)
            yield self.env.timeout(0)  # Must yield for simpy process
        elif isinstance(packet, RerrPacket):
            self.handle_rerr(packet, sender_id)
            yield self.env.timeout(0)  # Must yield for simpy process
        elif isinstance(packet, DataPacket):
            yield self.env.process(self.handle_data(packet, sender_id))
        elif isinstance(packet, AckPacket):
            # Ack handled by MAC, but passed here if needed?
            # Usually MAC handles Ack and calls penalize on failure.
            yield self.env.timeout(0)  # Must yield for simpy process

    def handle_rreq(self, rreq, sender_id):
        # 1. Check duplicates
        if (rreq.src_drone.identifier, rreq.broadcast_id) in self.seen_rreqs:
            return
        self.seen_rreqs[(rreq.src_drone.identifier, rreq.broadcast_id)] = self.env.now + self.PATH_DISCOVERY_TIME
        
        # 2. Update reverse route to Source
        self.update_route(rreq.src_drone.identifier, sender_id, rreq.hop_count + 1, rreq.src_seq)
        
        # 3. Check if I am Dest or have route to Dest
        is_dest = (rreq.dest_id == self.my_drone.identifier)
        has_fresh_route = False
        if rreq.dest_id in self.routing_table:
            entry = self.routing_table[rreq.dest_id]
            if entry['expiry_time'] > self.env.now and entry['seq_num'] >= rreq.dest_seq:
                has_fresh_route = True
                
        if is_dest or has_fresh_route:
            self.send_rrep(rreq, is_dest)
        else:
            # 4. Forward RREQ
            if rreq.get_current_ttl() < config.MAX_TTL:
                rreq.hop_count += 1
                rreq.increase_ttl()
                self.my_drone.transmitting_queue.put(rreq)

    def send_rrep(self, rreq, is_dest):
        dest_seq = self.seq_num if is_dest else self.routing_table[rreq.dest_id]['seq_num']
        if is_dest:
            self.seq_num += 1
            dest_seq = self.seq_num
            
        hop_count = 0 if is_dest else self.routing_table[rreq.dest_id]['hop_count']
        
        config.GL_ID_HELLO_PACKET += 1
        channel_id = self.my_drone.channel_assigner.channel_assign()
        
        rrep = RrepPacket(src_drone=self.my_drone,
                          creation_time=self.env.now,
                          packet_id=config.GL_ID_HELLO_PACKET,
                          packet_length=config.HELLO_PACKET_LENGTH,
                          simulator=self.simulator,
                          channel_id=channel_id,
                          originator_id=rreq.src_drone.identifier,
                          dest_id=rreq.dest_id,
                          dest_seq=dest_seq,
                          hop_count=hop_count,
                          lifetime=self.ACTIVE_ROUTE_TIMEOUT)
        
        # Unicast to next hop towards originator (which is sender of RREQ)
        # Wait, sender of RREQ is the previous hop.
        # We need route to originator. We just updated it in handle_rreq.
        next_hop = self.routing_table[rreq.src_drone.identifier]['next_hop']
        rrep.next_hop_id = next_hop
        
        logger.info(f"At time: {self.env.now} (us) ---- UAV: {self.my_drone.identifier} sends RREP for Dest: {rreq.dest_id} to NextHop: {next_hop}")
        self.my_drone.transmitting_queue.put(rrep)

    def handle_rrep(self, rrep, sender_id):
        # 1. Update route to Dest
        self.update_route(rrep.dest_id, sender_id, rrep.hop_count + 1, rrep.dest_seq)
        
        # 2. Check if I am Originator
        if rrep.originator_id == self.my_drone.identifier:
            # Send buffered packets
            if rrep.dest_id in self.packet_buffer:
                packets = self.packet_buffer[rrep.dest_id]
                del self.packet_buffer[rrep.dest_id]
                for pkt in packets:
                    pkt.next_hop_id = self.routing_table[rrep.dest_id]['next_hop']
                    self.my_drone.transmitting_queue.put(pkt)
        else:
            # 3. Forward RREP
            if rrep.originator_id in self.routing_table:
                next_hop = self.routing_table[rrep.originator_id]['next_hop']
                rrep.next_hop_id = next_hop
                rrep.hop_count += 1
                rrep.increase_ttl()
                self.my_drone.transmitting_queue.put(rrep)

    def handle_rerr(self, rerr, sender_id):
        # Invalidate routes
        for dest_id, dest_seq in rerr.unreachable_dests:
            if dest_id in self.routing_table and self.routing_table[dest_id]['next_hop'] == sender_id:
                del self.routing_table[dest_id]
                # Forward RERR if needed (simplified: broadcast if I had a route)
                # For now, just invalidate.
                
    def handle_data(self, packet, sender_id):
        # Similar to DSDV packet reception
        if packet.dst_drone.identifier == self.my_drone.identifier:
            # Arrived
            if packet.packet_id not in self.simulator.metrics.datapacket_arrived:
                self.simulator.metrics.calculate_metrics(packet)
                logger.info(f'At time: {self.env.now} (us) ---- Data packet: {packet.packet_id} reached Dest: {self.my_drone.identifier}')
            
            # Send ACK
            config.GL_ID_ACK_PACKET += 1
            src_drone = self.simulator.drones[sender_id]
            ack_packet = AckPacket(src_drone=self.my_drone,
                                   dst_drone=src_drone,
                                   ack_packet_id=config.GL_ID_ACK_PACKET,
                                   ack_packet_length=config.ACK_PACKET_LENGTH,
                                   ack_packet=packet,
                                   simulator=self.simulator,
                                   channel_id=packet.channel_id)
            
            yield self.env.timeout(config.SIFS_DURATION)
            
            if not self.my_drone.sleep:
                ack_packet.increase_ttl()
                self.my_drone.mac_protocol.phy.unicast(ack_packet, sender_id)
                yield self.env.timeout(ack_packet.packet_length / config.BIT_RATE * 1e6)
                self.simulator.drones[sender_id].receive()
        else:
            # Forward
            if packet.dst_drone.identifier in self.routing_table:
                if self.my_drone.transmitting_queue.qsize() < self.my_drone.max_queue_size:
                    logger.info(f'At time: {self.env.now} (us) ---- Data packet: {packet.packet_id} is received by next hop UAV: {self.my_drone.identifier}')
                    
                    self.my_drone.transmitting_queue.put(packet)
                    
                    config.GL_ID_ACK_PACKET += 1
                    src_drone = self.simulator.drones[sender_id]
                    ack_packet = AckPacket(src_drone=self.my_drone,
                                           dst_drone=src_drone,
                                           ack_packet_id=config.GL_ID_ACK_PACKET,
                                           ack_packet_length=config.ACK_PACKET_LENGTH,
                                           ack_packet=packet,
                                           simulator=self.simulator,
                                           channel_id=packet.channel_id)
                    
                    yield self.env.timeout(config.SIFS_DURATION)
                    
                    if not self.my_drone.sleep:
                        ack_packet.increase_ttl()
                        self.my_drone.mac_protocol.phy.unicast(ack_packet, sender_id)
                        yield self.env.timeout(ack_packet.packet_length / config.BIT_RATE * 1e6)
                        self.simulator.drones[sender_id].receive()
            else:
                # No route - packet dropped
                pass

    def update_route(self, dest_id, next_hop, hop_count, seq_num):
        current_time = self.env.now
        update = False
        if dest_id not in self.routing_table:
            update = True
        else:
            entry = self.routing_table[dest_id]
            if seq_num > entry['seq_num']:
                update = True
            elif seq_num == entry['seq_num'] and hop_count < entry['hop_count']:
                update = True
                
        if update:
            self.routing_table[dest_id] = {
                'next_hop': next_hop,
                'hop_count': hop_count,
                'seq_num': seq_num,
                'expiry_time': current_time + self.ACTIVE_ROUTE_TIMEOUT
            }

    def penalize(self, packet):
        """Called by MAC on ACK timeout (Link Break)"""
        if isinstance(packet, DataPacket):
            next_hop = packet.next_hop_id
            # Invalidate routes using this next hop
            unreachable = []
            to_remove = []
            for dest_id, entry in self.routing_table.items():
                if entry['next_hop'] == next_hop:
                    unreachable.append((dest_id, entry['seq_num']))
                    to_remove.append(dest_id)
            
            for dest_id in to_remove:
                del self.routing_table[dest_id]
                
            if unreachable:
                # Send RERR
                config.GL_ID_HELLO_PACKET += 1
                rerr = RerrPacket(src_drone=self.my_drone,
                                  creation_time=self.env.now,
                                  packet_id=config.GL_ID_HELLO_PACKET,
                                  packet_length=config.HELLO_PACKET_LENGTH,
                                  simulator=self.simulator,
                                  channel_id=self.my_drone.channel_assigner.channel_assign(),
                                  unreachable_dests=unreachable)
                self.my_drone.transmitting_queue.put(rerr)

    def purge_routes(self):
        while True:
            yield self.env.timeout(1 * 1e6)
            current_time = self.env.now
            to_remove = []
            for dest_id, entry in self.routing_table.items():
                if current_time > entry['expiry_time']:
                    to_remove.append(dest_id)
            for dest_id in to_remove:
                del self.routing_table[dest_id]
