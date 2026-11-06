# Task 5: Subnetting and Network Access Control

Block: `10.20.0.0/16`. Largest requirement first, each subnet placed right after the previous one,
smallest prefix that fits. Usable hosts = 2^(32 - prefix) - 2.

## Working

| Subnet | Hosts needed | Smallest prefix | Reasoning |
|---|---|---|---|
| app | 1,000 | /22 | /23 gives 2^9 - 2 = 510 (too few); /22 gives 2^10 - 2 = 1,022 |
| public | 250 | /24 | /25 gives 2^7 - 2 = 126 (too few); /24 gives 2^8 - 2 = 254 |
| data | 100 | /25 | /26 gives 2^6 - 2 = 62 (too few); /25 gives 2^7 - 2 = 126 |
| management | 20 | /27 | /28 gives 2^4 - 2 = 14 (too few); /27 gives 2^5 - 2 = 30 |

Placement: app starts at 10.20.0.0 and spans 1,024 addresses (10.20.0.0 - 10.20.3.255);
public starts at 10.20.4.0 (256 addresses); data starts at 10.20.5.0 (128 addresses);
management starts at 10.20.5.128 (32 addresses).

## Table

| Subnet | Network address | Prefix | Usable host range | Broadcast | Usable hosts |
|---|---|---|---|---|---|
| app | 10.20.0.0 | /22 | 10.20.0.1 - 10.20.3.254 | 10.20.3.255 | 1,022 |
| public | 10.20.4.0 | /24 | 10.20.4.1 - 10.20.4.254 | 10.20.4.255 | 254 |
| data | 10.20.5.0 | /25 | 10.20.5.1 - 10.20.5.126 | 10.20.5.127 | 126 |
| management | 10.20.5.128 | /27 | 10.20.5.129 - 10.20.5.158 | 10.20.5.159 | 30 |

## NACL for the public subnet (`network/nacl.json`)

Inbound (lowest number first, first match wins, default deny):

| Rule | Action | Protocol / port | Source | Purpose |
|---|---|---|---|---|
| 100 | deny | all | 198.51.100.0/24 | abusive range, blocked before any allow |
| 110 | allow | TCP 80 | 0.0.0.0/0 | HTTP |
| 120 | allow | TCP 443 | 0.0.0.0/0 | HTTPS |
| 130 | allow | TCP 22 | 10.20.5.128/27 (management) | SSH from management only |
| 140 | allow | TCP 1024-65535 | 10.20.0.0/22 (app) | replies from the app subnet (ephemeral ports) |

Outbound:

| Rule | Action | Protocol / port | Destination | Purpose |
|---|---|---|---|---|
| 100 | allow | TCP 8000 | 10.20.0.0/22 (app) | load balancer to the service |
| 110 | allow | TCP 1024-65535 | 0.0.0.0/0 | replies to clients (ephemeral ports) |

Check: `python tools/nacl_sim.py network/nacl.json network/packets_sample.jsonl --check`

## Explanation

A NACL is stateless: it does not remember that an inbound request was allowed, so the reply is a
new packet that is judged on its own. That is why replies need explicit rules of their own: an
outbound rule for ephemeral ports 1024-65535 back to clients, and an inbound rule for the replies
coming back from the app subnet. (A stateful security group would allow these automatically.)

Rules are evaluated from the lowest number upward and the first match decides. The deny for
198.51.100.0/24 is rule 100, lower than the allows for ports 80 and 443 (rules 110 and 120). If
it were numbered higher, a packet from that range to port 443 would match the allow rule first
and the block would never take effect.
