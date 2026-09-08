# templates/demo.tape - the README's terminal demo, recorded with Charm VHS.
#
#   brew install vhs ttyd ffmpeg     # or: https://github.com/charmbracelet/vhs
#   vhs docs/demo.tape               # writes docs/demo.gif
#
# Copy this to docs/demo.tape, replace the four commands, and commit it. The
# script is the point: a GIF nobody can regenerate becomes a lie the first time
# the command surface changes, and there is no way to tell from the image.
#
# Keep it SHORT and keep it REAL. Every command below is one a new user actually
# runs, in the order they meet them, and all of them are read-only -- `--help`
# and `--version` print, a doctor command diagnoses without repairing. A demo
# that mutates the recording machine is one nobody re-records, because
# re-recording costs them a clean machine.
#
# Re-record after any change to `--help`. Say so in the README, next to the link
# to this file, so the next contributor knows the asset has a trigger.

Output docs/demo.gif

Set Shell zsh
Set FontFamily "JetBrainsMono Nerd Font"
Set FontSize 18
Set Width 1100
Set Height 680
Set Padding 22
Set Theme "Catppuccin Mocha"
Set TypingSpeed 55ms
Set PlaybackSpeed 1.0

# VHS starts a NON-LOGIN shell, which never sources ~/.zshrc. If your entry
# point is a shell function rather than a binary on PATH, the whole recording is
# `command not found` without this line.
Hide
Type "source ~/.zshrc >/dev/null 2>&1" Enter
# Record from $HOME, not from wherever vhs was invoked: the prompt shows the
# working directory and the git branch, and a demo should not ship one
# contributor's checkout path or an in-flight branch name.
Type "cd ~" Enter
Type "clear" Enter
Show

Sleep 600ms

# 1. One command fronts the whole tool.
Type "yourtool" Sleep 400ms Enter
Sleep 3s

Type "clear" Enter
Sleep 300ms

# 2. What version is this, and where did it come from?
Type "yourtool --version" Sleep 400ms Enter
Sleep 2500ms

Type "clear" Enter
Sleep 300ms

# 3. The health check that proves the install landed.
Type "yourtool doctor" Sleep 400ms Enter
Sleep 4s

Type "clear" Enter
Sleep 300ms

# 4. The thing people actually came for.
Type "yourtool run --dry-run" Sleep 400ms Enter
Sleep 3500ms

Sleep 1s
