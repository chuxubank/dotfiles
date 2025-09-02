import time
import json
import struct
from mitmproxy import ctx, tcp
from mitmproxy.utils import strutils


class MQTTConfig:
    # MQTT subscribe topics to payload mappings
    TOPIC_PAYLOAD_MAP = {
        "home/sensors/temperature": {"temperature": 22.5, "unit": "C"},
        "home/sensors/humidity": {"humidity": 45, "unit": "%"},
        "home/devices/lamp": {"status": "on", "brightness": 75},
    }

    # Delay for responses
    DELAY_SECONDS = 1


class MQTTResponseHandler:
    def __init__(self):
        self.topic_payload_map = MQTTConfig.TOPIC_PAYLOAD_MAP

    def handle_publish(self, topic: str) -> bytes:
        """Return a payload based on the topic."""
        ctx.log.info(f"Handling PUBLISH for topic: {topic}")
        time.sleep(MQTTConfig.DELAY_SECONDS)

        # Generate response payload based on topic
        payload = self.topic_payload_map.get(topic, {"error": "Topic not supported"})
        ctx.log.debug(f"Response payload for topic '{topic}': {payload}")

        return json.dumps(payload).encode("utf-8")

    def handle_subscribe(self, flow):
        topic = flow.request.content.decode('utf-8')  # Assuming the topic is in the request content
        self.simulate_server_messages(topic)

    def simulate_server_messages(self, topic):
        # Simulate sending messages to the client for the subscribed topic
        for i in range(5):  # Send 5 simulated messages
            message = f"Simulated message {i + 1} for topic '{topic}'"
            self.send_message_to_client(topic, message)

    def send_message_to_client(self, topic, message):
        # Logic to send the message to the client
        # This would involve creating a TCPFlow or similar to send the message
        flow = tcp.TCPFlow()  # Create a TCPFlow instance
        flow.request.content = message.encode('utf-8')  # Set the message content
        flow.request.path = topic  # Set the topic as the path
        flow.response = flow.request  # Simulate response
        ctx.master.add_flow(flow)  # Add flow to the mitmproxy

    def publish_message(client, topic, message):
        # Publish a message to the specified MQTT topic
        client.publish(topic, message)
        ctx.log.debug(f"Published message to topic '{topic}': {message}")


# Global MQTT response handler
mqtt_handler = MQTTResponseHandler()


def tcp_message(flow: tcp.TCPFlow):
    """Handle MQTT TCP messages and log all topics and payloads."""
    try:
        message = flow.messages[-1]

        # Parse MQTT packet
        mqtt_packet = MQTTControlPacket(message.content)
        ctx.log.info(f"Processing MQTT message: {mqtt_packet.pprint()}")

        # Log topics and payloads based on packet type
        if mqtt_packet.packet_type == MQTTControlPacket.SUBSCRIBE:
            for topic, details in mqtt_packet.topic_filters.items():
                qos = details.get("qos", 0)
                ctx.log.info(f"SUBSCRIBE topic: {topic}, QoS: {qos}")
                mqtt_handler.handle_subscribe(flow)

        elif mqtt_packet.packet_type == MQTTControlPacket.PUBLISH:
            topic_name = mqtt_packet.topic_name.decode("utf-8")
            payload = mqtt_packet.payload.decode("utf-8", errors="replace")
            ctx.log.info(f"PUBLISH topic: {topic_name}, payload: {payload}")

        elif mqtt_packet.packet_type == MQTTControlPacket.UNSUBSCRIBE:
            for topic in mqtt_packet.topic_filters.keys():
                ctx.log.info(f"UNSUBSCRIBE topic: {topic}")

        # Log the payload if present
        if hasattr(mqtt_packet, "payload"):
            payload = mqtt_packet.payload
            if isinstance(payload, bytes):  # Raw bytes payload
                # Convert bytes to a string (UTF-8 or fallback to replace errors)
                payload_str = payload.decode("utf-8", errors="replace")
                ctx.log.info(f"Payload (bytes): {payload_str}")
            elif isinstance(payload, dict):  # Structured payload
                # Convert dict to JSON string for logging
                payload_str = json.dumps(payload, indent=2)
                ctx.log.info(f"Payload (dict): {payload_str}")
            else:  # Catch-all for other types (e.g., int, float, etc.)
                ctx.log.info(f"Payload (other): {payload}")

    except Exception as e:
        ctx.log.error(f"Error processing MQTT message: {e}")


class MQTTControlPacket:
    # Packet types
    (
        CONNECT,
        CONNACK,
        PUBLISH,
        PUBACK,
        PUBREC,
        PUBREL,
        PUBCOMP,
        SUBSCRIBE,
        SUBACK,
        UNSUBSCRIBE,
        UNSUBACK,
        PINGREQ,
        PINGRESP,
        DISCONNECT,
    ) = range(1, 15)

    # http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html#_Table_2.1_-
    Names = [
        "reserved",
        "CONNECT",
        "CONNACK",
        "PUBLISH",
        "PUBACK",
        "PUBREC",
        "PUBREL",
        "PUBCOMP",
        "SUBSCRIBE",
        "SUBACK",
        "UNSUBSCRIBE",
        "UNSUBACK",
        "PINGREQ",
        "PINGRESP",
        "DISCONNECT",
        "reserved",
    ]

    PACKETS_WITH_IDENTIFIER = [
        PUBACK,
        PUBREC,
        PUBREL,
        PUBCOMP,
        SUBSCRIBE,
        SUBACK,
        UNSUBSCRIBE,
        UNSUBACK,
    ]

    def __init__(self, packet):
        self._packet = packet
        # Fixed header
        # http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html#_Toc398718020
        self.packet_type = self._parse_packet_type()
        self.packet_type_human = self.Names[self.packet_type]
        self.dup, self.qos, self.retain = self._parse_flags()
        self.remaining_length = self._parse_remaining_length()
        # Variable header & Payload
        # http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html#_Toc398718024
        # http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html#_Toc398718026
        if self.packet_type == self.CONNECT:
            self._parse_connect_variable_headers()
            self._parse_connect_payload()
        elif self.packet_type == self.PUBLISH:
            self._parse_publish_variable_headers()
            self._parse_publish_payload()
        elif self.packet_type == self.SUBSCRIBE:
            self._parse_subscribe_variable_headers()
            self._parse_subscribe_payload()
        elif self.packet_type == self.SUBACK:
            pass
        elif self.packet_type == self.UNSUBSCRIBE:
            pass
        else:
            self.payload = None

    def pprint(self):
        s = f"[{self.Names[self.packet_type]}]"

        if self.packet_type == self.CONNECT:
            s += f"""

Client Id: {self.payload['ClientId']}
Will Topic: {self.payload.get('WillTopic')}
Will Message: {strutils.bytes_to_escaped_str(self.payload.get('WillMessage', b'None'))}
User Name: {self.payload.get('UserName')}
Password: {strutils.bytes_to_escaped_str(self.payload.get('Password', b'None'))}
"""
        elif self.packet_type == self.SUBSCRIBE:
            s += " sent topic filters: "
            s += ", ".join([f"'{tf}'" for tf in self.topic_filters])
        elif self.packet_type == self.PUBLISH:
            topic_name = strutils.bytes_to_escaped_str(self.topic_name)
            payload = strutils.bytes_to_escaped_str(self.payload)

            s += f" '{payload}' to topic '{topic_name}'"
        elif self.packet_type in [self.PINGREQ, self.PINGRESP]:
            pass
        else:
            s = f"Packet type {self.Names[self.packet_type]} is not supported yet!"

        return s

    def _parse_length_prefixed_bytes(self, offset):
        field_length_bytes = self._packet[offset : offset + 2]
        field_length = struct.unpack("!H", field_length_bytes)[0]

        field_content_bytes = self._packet[offset + 2 : offset + 2 + field_length]

        return field_length + 2, field_content_bytes

    def _parse_publish_variable_headers(self):
        offset = len(self._packet) - self.remaining_length

        field_length, field_content_bytes = self._parse_length_prefixed_bytes(offset)
        self.topic_name = field_content_bytes

        if self.qos in [0x01, 0x02]:
            offset += field_length
            self.packet_identifier = self._packet[offset : offset + 2]

    def _parse_publish_payload(self):
        fixed_header_length = len(self._packet) - self.remaining_length
        variable_header_length = 2 + len(self.topic_name)

        if self.qos in [0x01, 0x02]:
            variable_header_length += 2

        offset = fixed_header_length + variable_header_length

        self.payload = self._packet[offset:]

    def _parse_subscribe_variable_headers(self):
        self._parse_packet_identifier()

    def _parse_subscribe_payload(self):
        offset = len(self._packet) - self.remaining_length + 2

        self.topic_filters = {}

        while len(self._packet) - offset > 0:
            field_length, topic_filter_bytes = self._parse_length_prefixed_bytes(offset)
            offset += field_length

            qos = self._packet[offset : offset + 1]
            offset += 1

            topic_filter = topic_filter_bytes.decode("utf-8")
            self.topic_filters[topic_filter] = {"qos": qos}

    # http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html#_Toc398718030
    def _parse_connect_variable_headers(self):
        offset = len(self._packet) - self.remaining_length

        self.variable_headers = {}
        self.connect_flags = {}

        self.variable_headers["ProtocolName"] = self._packet[offset : offset + 6]
        self.variable_headers["ProtocolLevel"] = self._packet[offset + 6 : offset + 7]
        self.variable_headers["ConnectFlags"] = self._packet[offset + 7 : offset + 8]
        self.variable_headers["KeepAlive"] = self._packet[offset + 8 : offset + 10]
        # http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html#_Toc385349229
        self.connect_flags["CleanSession"] = bool(
            self.variable_headers["ConnectFlags"][0] & 0x02
        )
        self.connect_flags["Will"] = bool(
            self.variable_headers["ConnectFlags"][0] & 0x04
        )
        self.will_qos = (self.variable_headers["ConnectFlags"][0] >> 3) & 0x03
        self.connect_flags["WillRetain"] = bool(
            self.variable_headers["ConnectFlags"][0] & 0x20
        )
        self.connect_flags["Password"] = bool(
            self.variable_headers["ConnectFlags"][0] & 0x40
        )
        self.connect_flags["UserName"] = bool(
            self.variable_headers["ConnectFlags"][0] & 0x80
        )

    # http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html#_Toc398718031
    def _parse_connect_payload(self):
        fields = []
        offset = len(self._packet) - self.remaining_length + 10

        while len(self._packet) - offset > 0:
            field_length, field_content = self._parse_length_prefixed_bytes(offset)
            fields.append(field_content)
            offset += field_length

        self.payload = {}

        for f in fields:
            # http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html#_Toc385349242
            if "ClientId" not in self.payload:
                self.payload["ClientId"] = f.decode("utf-8")
            # http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html#_Toc385349243
            elif self.connect_flags["Will"] and "WillTopic" not in self.payload:
                self.payload["WillTopic"] = f.decode("utf-8")
            elif self.connect_flags["Will"] and "WillMessage" not in self.payload:
                self.payload["WillMessage"] = f
            elif self.connect_flags["UserName"] and "UserName" not in self.payload:
                self.payload["UserName"] = f.decode("utf-8")
            elif self.connect_flags["Password"] and "Password" not in self.payload:
                self.payload["Password"] = f
            else:
                raise Exception("")

    def _parse_packet_type(self):
        return self._packet[0] >> 4

    # http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html#_Toc398718022
    def _parse_flags(self):
        dup = None
        qos = None
        retain = None

        if self.packet_type == self.PUBLISH:
            dup = (self._packet[0] >> 3) & 0x01
            qos = (self._packet[0] >> 1) & 0x03
            retain = self._packet[0] & 0x01

        return dup, qos, retain

    # http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html#_Table_2.4_Size
    def _parse_remaining_length(self):
        multiplier = 1
        value = 0
        i = 1

        while True:
            encodedByte = self._packet[i]
            value += (encodedByte & 127) * multiplier
            multiplier *= 128

            if multiplier > 128 * 128 * 128:
                raise Exception("Malformed Remaining Length")

            if encodedByte & 128 == 0:
                break

            i += 1

        return value

    # http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html#_Table_2.5_-
    def _parse_packet_identifier(self):
        offset = len(self._packet) - self.remaining_length
        self.packet_identifier = self._packet[offset : offset + 2]

    def serialize(self):
        """Reconstruct the MQTT packet from its components."""
        # Serialize the fixed header
        flags = 0
        if self.packet_type == self.PUBLISH:
            flags = (self.dup << 3) | (self.qos << 1) | self.retain
        fixed_header = bytes(
            [(self.packet_type << 4) | flags]
        ) + self._encode_remaining_length(self.remaining_length)

        # Serialize the variable header and payload
        if self.packet_type == self.PUBLISH:
            variable_header = struct.pack("!H", len(self.topic_name)) + self.topic_name
            if self.qos in [0x01, 0x02]:
                variable_header += self.packet_identifier
            payload = self.payload
            return fixed_header + variable_header + payload

        # For other packet types, return the original packet for now
        return self._packet

    def _encode_remaining_length(self, length):
        """Encode the remaining length field as per MQTT spec."""
        encoded = bytearray()
        while True:
            byte = length % 128
            length //= 128
            if length > 0:
                byte |= 0x80
            encoded.append(byte)
            if length <= 0:
                break
        return encoded

    @staticmethod
    def create_publish_packet(topic: str, payload: bytes, qos: int = 0) -> bytes:
        """Create a PUBLISH packet for MQTT."""
        fixed_header = (MQTTControlPacket.PUBLISH << 4) | (qos << 1)
        topic_length = len(topic)
        topic_bytes = struct.pack("!H", topic_length) + topic.encode("utf-8")

        if qos > 0:
            packet_identifier = struct.pack("!H", 1)  # Example packet identifier
        else:
            packet_identifier = b""

        remaining_length = len(topic_bytes) + len(packet_identifier) + len(payload)
        remaining_length_bytes = b""

        # Encode remaining length
        while remaining_length > 0:
            byte = remaining_length % 128
            remaining_length //= 128
            if remaining_length > 0:
                byte |= 128
            remaining_length_bytes += struct.pack("B", byte)

        # Combine all parts
        packet = (
            struct.pack("B", fixed_header)
            + remaining_length_bytes
            + topic_bytes
            + packet_identifier
            + payload
        )
        return packet
