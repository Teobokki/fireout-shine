FIREOUT SHINE v1.0.5: SHINE ONLINE + SHINE SFC 27

SHINE ONLINE (phone ONLINE app, laptop SHINE ONLINE app, pause menu SHINE ONLINE)
- Real internet multiplayer with no account and no paid server. The host taps HOST A SESSION and gets a join code such as SHINE-XXXX-XXXX (or a longer SHINE-XXXX-XXXX-XXXX when the router changes the port). Friends type that code under JOIN WITH A CODE.
  - The game asks public STUN servers for the host's internet address and asks the router (UPnP) to open UDP 47115. The joiner then punches through with signed packets (UDP hole punching).
  - Strict router: the joiner shows a REPLY CODE, and the host enters it under LET A FRIEND IN to punch back.
  - If nothing gets through, the game says exactly which UDP port the host should forward.
  - On the same Wi-Fi, LAN SESSIONS lists games automatically.
- Every packet is signed with HMAC-SHA256 using a key from the join code plus the optional password; anything else is ignored. A wrong password is reported as such.
- Session tools: host, join, friends list with ping, KICK (host only), LEAVE or CLOSE SESSION, chat (SAY), and a ping/status line on the HUD.
- Positions, walking and running, cars (each player's car is shown as they drive), chat and character choices all sync.
- Friends play as NEW characters, never as ANA or DANIEL: 8 presets (KAITO, RIN, JUNO, OBI, SORA, LENA, TAKU, MAYA) plus a customiser for name, skin tone, hair style and colour, top style and colour, bottoms and accessory (glasses, cap, headphones, beanie). Your look is saved.
- BRING THEM IN: AI friends from the same character pool follow you in a group, wander nearby when you stop, drive their own cars after yours, and play for your team in SHINE SFC 27. SEND AI FRIENDS HOME removes them.

SHINE SFC 27 football
- The new SHINE SFC 27 STADIUM on HIKARI BEACH has:
  - a full-size 105 x 68 m pitch with standard white markings (centre circle, penalty and goal areas, penalty spots and arcs, corner arcs and flags), goals with nets, advertising boards, four stands with a crowd, roofs and plain floodlight masts with no glow
  - the gate sign SHINE SFC 27 STADIUM, an [E] PLAY SHINE SFC 27 prompt at the entrance, and an F icon on the map
- Modes: PLAY VS AI, or (as host) ONLINE: ALL OF US VS AI or ONLINE: SPLIT TEAMS. AI fills every empty spot (7-a-side). Pick your club, the opponent, and a match length of 2, 4, 6 or 8 minutes (90' on the clock).
- Controls: WASD move, SPACE pass, F shoot, R tackle, SHIFT sprint. There are also on-screen PASS / SHOOT / TACKLE / SPRINT buttons, a stamina bar, a scoreboard and clock, kickoff, goals, saves, throw-ins, corners, goal kicks, FULL TIME with the scorers, and PLAY AGAIN or LEAVE STADIUM.
- Fictional clubs: SHINE TOKYO FC, HIKARI BEACH UNITED, NEON HARBOUR CITY, SAKURA HILL ROVERS, KUROGANE ATHLETIC and AKARI WANDERERS.

JP TAXI
- New destination: SHINE ONLINE SFC 27 FOOTBALL PITCH. You're dropped at the stadium gate.

Internet play limits
- With no relay server, two players behind strict or symmetric NAT, or carrier-grade NAT, may not connect directly. Try the REPLY CODE; if it still fails, the host must forward UDP 47115, or the port shown in the app.
- Windows may ask to let FIREOUT SHINE through the firewall the first time. Choose Allow.
- Up to 8 players per session. The host runs the football match, and friends see it with their own ping.

ANA (with BUILD and TSUNAMI) and DANIEL are unchanged. While you're a guest in someone's session you play as your SHINE ONLINE character, and your crew comes back when you leave.
