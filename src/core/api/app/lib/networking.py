import socket


def resolve_ip(hostname):
    return socket.gethostbyname(hostname)
