#!/bin/zsh
cd -- "$(dirname -- "$0")/../.." || exit 1
exec python3 -m projects.xiaogj-web.tools.exploration_tree --open "$@"
