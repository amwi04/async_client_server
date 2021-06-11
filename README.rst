Raft implementation (still in progress)

    - https://pdos.csail.mit.edu/6.824/schedule.html
    - https://www.youtube.com/channel/UC_7WrbZTCODu1o_kfUMq88g/videos


clients:
    - quit -> Disconnect to the server
    - make primary -> will make the server primary
    - join {host:port} -> will join the host and update it on every server
    - check_peers -> will ping all server and return result
    - peers_list -> list all the servers in node
    