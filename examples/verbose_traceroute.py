'''
    icmplib
    ~~~~~~~

    A powerful library for forging ICMP packets and performing ping
    and traceroute.

        https://github.com/ValentinBELYN/icmplib

    :copyright: Copyright 2017-2021 Valentin BELYN.
    :license: GNU LGPLv3, see the LICENSE for details.

    ~~~~~~~

    Example: verbose traceroute (advanced)

    Traceroute to ovh.com (198.27.92.1): 56 data bytes, 30 hops max

        1    192.168.0.254      192.168.0.254                9.86 ms
        2    194.149.164.56     194.149.164.56               4.61 ms
        3    213.186.32.181     be100-159.th2-1-a9.fr.eu     11.97 ms
        4    94.23.122.146      be102.rbx-g1-nc5.fr.eu       15.81 ms
        5    * * *
        6    37.187.231.75      be5.rbx-iplb1-a70.fr.eu      17.12 ms
        7    198.27.92.1        www.ovh.com                  10.87 ms

    Completed.
'''

from socket import getfqdn
from time import sleep

from icmplib import ICMPv4Socket, ICMPv6Socket, ICMPRequest
from icmplib import ICMPLibError, TimeoutExceeded, TimeExceeded
from icmplib import PID, resolve, is_hostname, is_ipv6_address


def verbose_traceroute(address, count=2, interval=0.05, timeout=2,
        id=PID, max_hops=30):
    # We perform a DNS lookup if a hostname or an FQDN is passed in
    # parameters.
    if is_hostname(address):
        ip_address = resolve(address)[0]
    else:
        ip_address = address

    # A payload of 56 bytes is used by default. You can modify it using
    # the 'payload_size' parameter of your ICMP request.
    print(f'Traceroute to {address} ({ip_address}): '
          f'56 data bytes, {max_hops} hops max\n')

    # We detect the socket to use from the specified IP address
    if is_ipv6_address(ip_address):
        sock = ICMPv6Socket()
    else:
        sock = ICMPv4Socket()

    ttl = 1
    host_reached = False

    while not host_reached and ttl <= max_hops:
        for sequence in range(count):
            # We create an ICMP request
            request = ICMPRequest(
                destination=ip_address,
                id=id,
                sequence=sequence,
                ttl=ttl)

            try:
                # We send the request
                sock.send(request)

                # We are awaiting receipt of an ICMP reply
                reply = sock.receive(request, timeout)

                # We received a reply
                # We display some information
                source_name = getfqdn(reply.source)

                print(f'  {ttl:<2}    {reply.source:15}    '
                      f'{source_name:40}    ', end='')

                # We throw an exception if it is an ICMP error message
                reply.raise_for_status()

                # We reached the destination host
                # We calculate the round-trip time and we display it
                round_trip_time = (reply.time - request.time) * 1000
                print(round(round_trip_time, 2), 'ms')

                # We can stop the search
                host_reached = True
                break

            except TimeExceeded as err:
                # An ICMP Time Exceeded message has been received
                # The message was probably generated by an intermediate
                # gateway
                reply = err.reply

                # We calculate the round-trip time and we display it
                round_trip_time = (reply.time - request.time) * 1000
                print(round(round_trip_time, 2), 'ms')

                sleep(interval)
                break

            except TimeoutExceeded:
                # The timeout has been reached and no host or gateway
                # has responded after multiple attempts
                if sequence >= count - 1:
                    print(f'  {ttl:<2}    * * *')

            except ICMPLibError:
                # Other errors are ignored
                pass

        ttl += 1

    print('\nCompleted.')


# This function supports both FQDNs and IP addresses. See the 'resolve'
# function for details.
verbose_traceroute('ovh.com')
