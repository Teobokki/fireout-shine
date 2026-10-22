# FIREOUT SHINE 1.0.5.2: update fixes

- **Fixed the in-game update.**
  - The downloaded Setup is now started detached from %TEMP%, with a clean environment, before the game quits. Previously it was started from inside the game's own process.
  - The portable self-update helper also relaunches the new exe with a clean environment. The new version now really starts, and Windows no longer shows "Failed to remove temporary directory ...\_MEI...".
- Versions are compared with all four parts: 1.0.5 = 1.0.5.0 < 1.0.5.1 < 1.0.5.2.
- The Setup now closes a running FIREOUT SHINE before replacing files (CloseApplications=force). It still installs per-user to %LOCALAPPDATA%\Programs\FIREOUT SHINE with no admin rights, over any earlier version.
- Gameplay is the same as 1.0.5.1: SHINE ONLINE without admin, UNLIMITED SFC 27 matches with END MATCH, football kits.

©2026 EX Inc./HYPERION DIGITAL ©2026
