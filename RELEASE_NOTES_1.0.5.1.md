# FIREOUT SHINE 1.0.5.1

- **SHINE ONLINE without firewall hassle and without admin rights.** The installer is per-user again, with no UAC prompt, and installs to the same folder as 1.0.5.
  - Every connection now starts outbound: the guest calls the host, and the host calls the guest from their REPLY CODE. Keep-alives every 5 s hold the router and firewall mappings open.
  - Windows Firewall lets those replies through even if you dismiss or cancel its own prompt.
  - The game never asks you to click Allow.
- **LAN.** Hosts announce themselves from the game socket and also answer "anyone hosting?" broadcast queries.
- **SHINE SFC 27 match length is UNLIMITED by default.** The clock counts up with no full-time whistle.
  - END MATCH (Esc menu or the on-screen button) shows the final score screen, then LEAVE STADIUM takes you to the stadium gate.
  - Timed matches of 4, 8, 12 or 90 minutes are still available.
  - Online, the host's setting applies to everyone. The host's END MATCH ends the match for all players. A guest's LEAVE MATCH hands their player to the AI.
- Football kits now have proper shorts, socks and boots.
