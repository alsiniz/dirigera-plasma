# Security

DIRIGERA tokens act like passwords for the whole hub: a person who gets your token
can control other residents' devices with another program, even though this
application limits writes to individually approved device IDs and saved room IDs.

- The app stores the token in `~/.config/dirigera-plasma/config.json` (mode 0600).
  Treat it as a password. Protect account backups and don't upload this file.
- Room/group operations are implemented as individual device writes with
  authorization checks; the hub itself does not enforce this allowlist.
- This app does not listen on a TCP port, forward the token to an external
  service or require IKEA cloud access to control lights.
- To report a security vulnerability, do **not** create a public issue containing
  exploit details or credentials. Contact the repository maintainer privately
  through a GitHub private vulnerability report if enabled.
- If a token has been exposed, seek a revocation path through the hub's settings
  or reset authorization as appropriate. Creating another token alone may not
  invalidate the old one.
