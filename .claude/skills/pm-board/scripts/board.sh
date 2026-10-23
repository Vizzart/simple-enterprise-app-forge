#!/usr/bin/env bash
# Print the board grouped by column, with assignees.
# Usage: board.sh [--mine]
set -euo pipefail

source "$(dirname "$0")/../project.conf"

filter='.'
if [[ "${1:-}" == --mine ]]; then
  me=$(gh api user --jq .login)
  filter="select((.assignees // []) | index(\"$me\"))"
fi

gh project item-list "$PROJECT_NR" --owner "$PROJECT_OWNER" --limit 200 --format json --jq "
  [.items[] | $filter]
  | group_by(.status // \"No status\")
  | .[]
  | \"\n## \(.[0].status // \"No status\") (\(length))\",
    (.[] | \"  #\(.content.number // \"-\")  \(.title)  [\((.labels // []) | join(\", \"))]  @\((.assignees // []) | join(\",@\"))  \(.milestone.title // \"\")\")
"
