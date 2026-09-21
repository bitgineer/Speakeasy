#!/usr/bin/env sh
# Alias for install.sh. Sets up anything missing, then starts the app.
exec "$(dirname "$0")/install.sh" --launch "$@"
