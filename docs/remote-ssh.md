# Using claude-on-mac from Linux (remote mode)

This doc is for the case where your primary workstation is Linux (or any non-Mac host) and the Mac you want to reach lives elsewhere on your network. If Claude Code is running **on** the Mac, ignore this file — follow the normal one-paste flow in `README.md` and `AGENTS.md`.

## How it works

The nine Python helpers in `bin/` stay on the Mac, unchanged. On the Linux side, we install thin SSH shims under the same names (`imsg`, `cal`, `mail`, …). Each shim is a symlink to one bash script (`bin/remote/claude-on-mac-exec`) that forwards the invocation to your Mac over SSH.

```
Linux:  imsg recent 5
  → shim execs: ssh $CLAUDE_ON_MAC_TARGET imsg recent 5
  → Mac runs the real helper
  → stdout / stderr / exit code stream back through SSH
```

One SSH `ControlMaster` socket amortizes the handshake across calls — roughly **50 ms warm, 300 ms cold**. No daemon on either side; each call is one SSH exec.

**The consent contract is unchanged.** `imsg-send` and `mail-send` still default to dry-run, still require `--yes` per individual send, and the `CONSENT-GATED SEND` banner still prints to stderr immediately before a real transmit — except now stderr lands in your Linux terminal instead of the Mac's. Transport has no effect on consent.

## When to use this

- Your daily driver is Linux / a DGX / another Mac, and the target Mac is a different machine.
- You can reach the target Mac over Tailscale (recommended) or over the same LAN via Bonjour/mDNS.
- SSH-exposed-to-the-public-internet is **not supported**. Don't do that.

## Reachability requirement

One of these must be true:

- **Tailscale on both machines, same tailnet.** Recommended. MagicDNS gives you a stable hostname (`mac.tail1234.ts.net`) that works from anywhere. Tailscale SSH, if enabled, eliminates SSH-key setup entirely.
- **Both machines on the same LAN**, and `mac.local` resolves via Bonjour/mDNS.

If neither is true, install Tailscale on both ends first and come back. We don't automate that; see `tailscale.com/download`.

## One-time Mac-side setup

**Prerequisite:** the normal `claude-on-mac` install (per `AGENTS.md`) must already be complete on the Mac. The helpers must exist under `~/bin` and pass a local `tcc-check` before you add SSH on top.

Then, on the Mac:

### 1. Enable Remote Login

```bash
sudo systemsetup -setremotelogin on
```

Or via GUI: System Settings → General → Sharing → Remote Login → **On**. Optionally restrict "Allow access for" to your user only.

### 2. Grant Full Disk Access to `sshd-keygen-wrapper`

Without this, every SQLite-reading helper (`imsg`, `contacts`, `note`, `mail`) fails when invoked over SSH. TCC treats sshd as a different security context from your Terminal, so the FDA grant you gave during the normal install **does not cover** incoming SSH sessions.

1. System Settings → Privacy & Security → Full Disk Access.
2. Click the **+** button.
3. Press **Cmd+Shift+G** to open the path-entry field.
4. Paste: `/usr/libexec/sshd-keygen-wrapper`
5. Click **Add**, then toggle the switch **on**.
6. Enter your admin password when prompted.

You do not need to restart anything; new SSH sessions pick up the grant immediately.

### 3. Warm the per-app Automation grants

This is the subtle part. Every write helper (`cal add`, `rem add`, `note new`, `mail-send`, `imsg-send`) drives a Mac app through AppleScript. Each (source process → target app) pair needs its own Automation grant. Those grants are approved via a system dialog that only fires when a GUI session is present — SSH sessions can't pop them.

The fix is to warm the grants under the sshd TCC context by triggering each probe from SSH and then approving the resulting dialog **at the Mac's console**:

1. From your Linux box, SSH in and run `tcc-check` once. Expect one or more ❌ on the Automation probes (Calendar, Reminders, Notes, Mail).
2. Walk over to the Mac. For each failing app, run the same AppleScript probe locally in Terminal — for example:
   ```bash
   osascript -e 'tell application "Calendar" to return (count of calendars)'
   osascript -e 'tell application "Reminders" to return (count of lists)'
   osascript -e 'tell application "Notes" to return (count of folders)'
   osascript -e 'tell application "Mail" to return (count of accounts)'
   ```
3. Each will pop a TCC dialog — click **Allow**.
4. Back on Linux, rerun `ssh "$CLAUDE_ON_MAC_TARGET" tcc-check`. Everything should now be ✅.

This is a one-time ceremony. Once warmed, the grants persist.

### 4. Verify the Mac's non-interactive SSH PATH

SSH non-login sessions do NOT source `~/.zshrc` or `~/.bashrc`. They source `~/.zshenv` (zsh) or `~/.bash_profile` (bash). If `~/bin` isn't in the PATH those files export, your shims will fail with `command not found: imsg` even though `imsg` is installed.

Verify:

```bash
ssh "$CLAUDE_ON_MAC_TARGET" 'which imsg'
```

If it doesn't print a path, append this to `~/.zshenv` (or `~/.bash_profile` if the Mac user's login shell is bash) on the Mac:

```bash
export PATH="$HOME/bin:$PATH"
```

## Linux-side setup

On the Linux box:

```bash
git clone https://github.com/nixfred/claude-on-mac.git ~/claude-on-mac
mkdir -p ~/bin

# Symlink every shim in one shot:
ln -sf ~/claude-on-mac/bin/remote/* ~/bin/
```

Add `~/bin` to your PATH if it isn't already. If a different `imsg` is already on your PATH (e.g. the Rust `imsg` CLI some Macs/Linuxes have), make sure `~/bin` comes first — same namespace-collision gotcha as the local install (see `AGENTS.md` Step 3.5).

Set the target and persist it:

```bash
# Add to ~/.zshrc or ~/.bashrc:
export CLAUDE_ON_MAC_TARGET="user@mac.tail1234.ts.net"
```

Recommended: add a `Host` block to `~/.ssh/config` so any SSH session to the Mac shares the ControlMaster socket with the shims (including your own interactive sessions):

```
Host mac.tail1234.ts.net
  ControlMaster auto
  ControlPersist 10m
  ControlPath ~/.ssh/cm-%r@%h:%p
  ServerAliveInterval 30
```

## Smoke test

In order:

```bash
tcc-check                                    # expect all ✅
imsg recent 5                                 # normal output
cal week                                      # normal output
mail inbox 5                                  # normal output
contacts find <somebody>                      # normal output

imsg-send --self "proof"                      # dry-run text, nothing sent
imsg-send --self --yes "proof"                # CONSENT-GATED SEND banner on stderr, then 'sent.'
```

If the final step landed, confirm on the Mac side:

```bash
ssh "$CLAUDE_ON_MAC_TARGET" \
  'sqlite3 -readonly ~/Library/Messages/chat.db \
   "SELECT text FROM message WHERE is_from_me=1 ORDER BY date DESC LIMIT 1"'
```

## Known failure modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ssh: connect … Operation timed out` | Mac is asleep (or lid closed on a laptop) | Enable "Prevent automatic sleeping when the display is off"; or run `caffeinate -d` on the Mac; or ignore if intermittent use is acceptable. |
| Command hangs indefinitely | Stale ControlMaster socket after network change | `ssh -O exit "$CLAUDE_ON_MAC_TARGET"` then retry. |
| AppleScript error `-1743` | Automation grant missing under sshd TCC context | Re-do §3 (warming) for the specific app. |
| `command not found: imsg` on the remote | Mac's non-interactive SSH PATH lacks `~/bin` | §4 above: add `export PATH="$HOME/bin:$PATH"` to `~/.zshenv` or `~/.bash_profile` on the Mac. |
| Empty SQLite reads over SSH but local works | FDA granted to Terminal but NOT to sshd-keygen-wrapper | §2 above. |
| `ssh: connect to host … port 22: Connection refused` | Remote Login disabled | §1 above. |
| `imsg-send --yes` reports success but no banner seen | You ran it inside a pipe that swallows stderr | Rerun without the pipe, or `2>&1`. The banner is load-bearing; never suppress it. |

## What's NOT here

- **Apple Journal.** Same as local mode: no write API exists. See `docs/journal.md`.
- **Health.** Same as local: only via user-authored Shortcuts.
- **GUI AppleScript when the Mac console is logged out or at the login window.** Some app scripts fail in that state; solvable only by keeping the Mac user logged in.

## If you get lost

Re-read this file top to bottom. Then `docs/tcc-permissions.md` for the local TCC model (useful context for why sshd needs its own grants). Then `AGENTS.md` for the normal Mac-side install the shim depends on.
