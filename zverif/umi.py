class UmiPacket:
    def __init__(self, opcode: int=0, size: int=0, user: int=0, dstaddr: int=0,
        srcaddr: int=0, data: int=0):

        self.opcode = opcode
        self.size = size
        self.user = user
        self.dstaddr = dstaddr
        self.srcaddr = srcaddr
        self.data = data
    
    def pack(self) -> bytes:
         # pack command
        cmd = 0
        cmd |= (self.opcode & ((1<< 8)-1)) << 0
        cmd |= (self.size   & ((1<< 4)-1)) << 8
        cmd |= (self.user   & ((1<<20)-1)) << 12

        # convert everything to bytearrays
        cmd = cmd.to_bytes(4, 'little')
        dstaddr = self.dstaddr.to_bytes(8, 'little')
        data = self.data.to_bytes(16, 'little')

        # order things appropriately
        packet = bytes([])
        packet += cmd
        packet += dstaddr[0:4]
        packet += bytes([0]*4)
        packet += data
        packet += dstaddr[4:8]

        # make sure the packet is formatted properly
        assert len(packet) == 32, 'Packet must be exactly 32 bytes long.'

        # return formatted packet
        return packet
    
    @classmethod
    def unpack(cls, packet: bytes):
        # extract addr, data, command as bytes    
        addr = int.from_bytes((packet[4:8] + packet[28:32]), 'little')
        data = int.from_bytes(packet[12:27], 'little')
        cmd = int.from_bytes(packet[0:4], 'little')

        # unpack the command
        opcode = (cmd >>  0) & ((1<< 8)-1)
        size   = (cmd >>  8) & ((1<< 4)-1)
        user   = (cmd >> 12) & ((1<<20)-1)

        # return object representing the packet
        return cls(opcode=opcode, size=size, user=user, dstaddr=addr, data=data)