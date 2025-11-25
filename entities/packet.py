from utils import config


class Packet:
    """
    Basic properties of the packet

    all other packets need to inherit this class

    Attributes:
        packet_id: identifier of the packet, used to uniquely represent a packet
        creation_time: the generation time of the packet
        deadline: maximum segment lifetime of packet, in second
        __ttl: current "Time to live (TTL)"
        number_retransmission_attempt: record the number of retransmissions of packet on different drones
        waiting_start_time: the time at which tha packet is added to the "transmitting queue" of drone
        first_attempt_time: the time at which the packet starts the backoff stage
        transmitting_start_time: the time at which the packet can be transmitted to the channel after backoff
        time_delivery: the time at which the packet arrives at its destination
        time_transmitted_at_last_hop: the transmitting time at last drone
        transmission_mode: unicast or multicast or broadcast?
        channel_id: the identity of the channel that used to transmit this packet

    Author: Zihao Zhou, eezihaozhou@gmail.com
    Created at: 2024/1/11
    Updated at: 2025/3/30
    """

    def __init__(self,
                 packet_id,
                 packet_length,
                 creation_time,
                 simulator,
                 channel_id):

        self.packet_id = packet_id
        self.packet_length = packet_length
        self.creation_time = creation_time
        self.deadline = config.PACKET_LIFETIME
        self.simulator = simulator
        self.channel_id = channel_id
        self.__ttl = 0

        self.number_retransmission_attempt = {}

        for drone in self.simulator.drones:
            self.number_retransmission_attempt[drone.identifier] = 0  # initialization

        # for calculating the queuing delay
        self.waiting_start_time = None
        self.first_attempt_time = None
        self.transmitting_start_time = None

        self.time_delivery = None  # for end-to-end delay
        self.time_transmitted_at_last_hop = 0
        self.transmission_mode = None

        self.intermediate_drones = []

    def increase_ttl(self):
        self.__ttl += 1

    def get_current_ttl(self):
        return self.__ttl


class DataPacket(Packet):
    """
    Basic properties of the data packet

    Attributes:
        src_drone: source drone that originates the data packet
        dst_drone: destination drone of this data packet
        routing_path: record to whole routing path in centralized routing protocol
        next_hop_id: identifier of the next hop drone

    Author: Zihao Zhou, eezihaozhou@gmail.com
    Created at: 2024/1/11
    Updated at: 2025/3/30
    """

    def __init__(self,
                 src_drone,
                 dst_drone,
                 creation_time,
                 data_packet_id,
                 data_packet_length,
                 simulator,
                 channel_id):
        super().__init__(data_packet_id, data_packet_length, creation_time, simulator, channel_id)

        self.src_drone = src_drone
        self.dst_drone = dst_drone

        self.routing_path = None  # for centralized routing protocols
        self.next_hop_id = None  # next hop for this data packet


class AckPacket(Packet):
    def __init__(self,
                 src_drone,
                 dst_drone,
                 ack_packet_id,
                 ack_packet_length,
                 ack_packet,
                 simulator,
                 channel_id,
                 creation_time=None):
        super().__init__(ack_packet_id, ack_packet_length, creation_time, simulator, channel_id)

        self.src_drone = src_drone
        self.dst_drone = dst_drone

        self.ack_packet = ack_packet


class HelloPacket(Packet):
    """
    Hello packet for neighbor discovery
    """
    def __init__(self,
                 src_drone,
                 creation_time,
                 packet_id,
                 packet_length,
                 simulator,
                 channel_id):
        super().__init__(packet_id, packet_length, creation_time, simulator, channel_id)
        self.src_drone = src_drone
        self.transmission_mode = 1  # Broadcast


class RreqPacket(Packet):
    """
    Route Request Packet for AODV
    """
    def __init__(self, src_drone, creation_time, packet_id, packet_length, simulator, channel_id,
                 broadcast_id, dest_id, dest_seq, src_seq, hop_count=0):
        super().__init__(packet_id, packet_length, creation_time, simulator, channel_id)
        self.src_drone = src_drone
        self.broadcast_id = broadcast_id
        self.dest_id = dest_id
        self.dest_seq = dest_seq
        self.src_seq = src_seq
        self.hop_count = hop_count
        self.transmission_mode = 1  # Broadcast

class RrepPacket(Packet):
    """
    Route Reply Packet for AODV
    """
    def __init__(self, src_drone, creation_time, packet_id, packet_length, simulator, channel_id,
                 originator_id, dest_id, dest_seq, hop_count, lifetime):
        super().__init__(packet_id, packet_length, creation_time, simulator, channel_id)
        self.src_drone = src_drone
        self.originator_id = originator_id
        self.dest_id = dest_id
        self.dest_seq = dest_seq
        self.hop_count = hop_count
        self.lifetime = lifetime
        self.next_hop_id = None  # Set by routing protocol
        self.transmission_mode = 0  # Unicast

class RerrPacket(Packet):
    """
    Route Error Packet for AODV
    """
    def __init__(self, src_drone, creation_time, packet_id, packet_length, simulator, channel_id,
                 unreachable_dests):
        super().__init__(packet_id, packet_length, creation_time, simulator, channel_id)
        self.src_drone = src_drone
        self.unreachable_dests = unreachable_dests  # List of (dest_id, dest_seq)
        self.transmission_mode = 1  # Broadcast (usually)
