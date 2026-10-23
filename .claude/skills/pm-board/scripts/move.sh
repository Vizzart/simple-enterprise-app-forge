#!/usr/bin/env bash
# Move an issue's card on the board. Adds the issue to the board if missing.
# Moving to "progress" assigns the issue to the current gh user when it has no assignee.
# Usage: move.sh <issue-number> <todo|progress|test|done>
set -euo pipefail

source "$(dirname "$0")/../project.conf"

issue=${1:?usage: move.sh <issue-number> <todo|progress|test|done>}
target=${2:?usage: move.sh <issue-number> <todo|progress|test|done>}

case "$target" in
  todo)     column="Todo" ;;
  progress) column="In Progress" ;;
  test)     column="Test" ;;
  done)     column="Done" ;;
  *) echo "unknown status: $target (todo|progress|test|done)" >&2; exit 1 ;;
esac

repo=$(gh repo view --json nameWithOwner --jq .nameWithOwner)
project_id=$(gh project view "$PROJECT_NR" --owner "$PROJECT_OWNER" --format json --jq .id)
field_id=$(gh project field-list "$PROJECT_NR" --owner "$PROJECT_OWNER" --format json \
  --jq '.fields[] | select(.name=="Status") | .id')
option_id=$(gh project field-list "$PROJECT_NR" --owner "$PROJECT_OWNER" --format json \
  --jq ".fields[] | select(.name==\"Status\") | .options[] | select(.name==\"$column\") | .id")

if [[ -z "$option_id" ]]; then
  echo "column '$column' not found on the board" >&2; exit 1
fi

# item-add returns the existing item when the issue is already on the board
item_id=$(gh project item-add "$PROJECT_NR" --owner "$PROJECT_OWNER" \
  --url "https://github.com/$repo/issues/$issue" --format json --jq .id)

gh project item-edit --project-id "$project_id" --id "$item_id" \
  --field-id "$field_id" --single-select-option-id "$option_id" >/dev/null

if [[ "$target" == progress ]] && \
   [[ $(gh issue view "$issue" --json assignees --jq '.assignees | length') == 0 ]]; then
  gh issue edit "$issue" --add-assignee @me >/dev/null
  echo "#$issue assigned to $(gh api user --jq .login)"
fi

echo "#$issue -> $column"
