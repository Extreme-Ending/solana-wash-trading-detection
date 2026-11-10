#!/usr/bin/env bash

set -euo pipefail
set -E

readonly SCRIPT_NAME="${0##*/}"

on_unexpected_error() {
    local exit_code=$?
    local line_number=$1

    printf '\n%s: unexpected failure near line %s (exit %s).\n' \
        "$SCRIPT_NAME" "$line_number" "$exit_code" >&2
    printf 'No history-rewriting recovery was attempted. Inspect the repository with '\''git status'\'' before continuing.\n' >&2
    exit "$exit_code"
}

trap 'on_unexpected_error "$LINENO"' ERR

die() {
    printf '%s: %s\n' "$SCRIPT_NAME" "$1" >&2
    exit "${2:-1}"
}

confirm() {
    local prompt=$1
    local reply

    read -r -p "$prompt [y/N] " reply || return 1
    case "$reply" in
        y|Y|yes|YES|Yes) return 0 ;;
        *) return 1 ;;
    esac
}

is_private_path() {
    local path=${1#./}
    local lower_path=${path,,}
    local base_name=${lower_path##*/}

    case "$path" in
        AGENTS.md|*/AGENTS.md|.agents|.agents/*|*/.agents/*|\
        CODEX_IMPLEMENTATION_PROMPT.md|*/CODEX_IMPLEMENTATION_PROMPT.md|\
        CODEX_PHASE_PROMPTS.md|*/CODEX_PHASE_PROMPTS.md)
            return 0
            ;;
    esac

    case "$base_name" in
        .env|.env.*)
            case "$base_name" in
                .env.example|.env.sample|.env.template) ;;
                *) return 0 ;;
            esac
            ;;
    esac

    case "$lower_path" in
        secrets|secrets/*|*/secrets|*/secrets/*|\
        .secrets|.secrets/*|*/.secrets|*/.secrets/*|\
        .aws|.aws/*|*/.aws|*/.aws/*|\
        .ssh|.ssh/*|*/.ssh|*/.ssh/*|\
        data/raw|data/raw/*|*/data/raw|*/data/raw/*|\
        raw_data|raw_data/*|*/raw_data|*/raw_data/*|\
        raw-data|raw-data/*|*/raw-data|*/raw-data/*|\
        nft.csv|*/nft.csv|nft_trades.csv|*/nft_trades.csv|\
        models|models/*|\
        artifacts/experimental|artifacts/experimental/*|\
        model_artifacts|model_artifacts/*|*/model_artifacts|*/model_artifacts/*)
            return 0
            ;;
    esac

    case "$base_name" in
        *.joblib|*.pkl|*.pickle|*.onnx|*.pt|*.pth|*.h5|*.keras|*.cbm|*.xgb|*.lgb|\
        *credential*.json|*service-account*.json|*service_account*.json|\
        firebase-adminsdk*.json|application_default_credentials.json|\
        *.pem|*.key|*.p12|*.pfx|id_rsa|id_ed25519|.npmrc|.pypirc)
            return 0
            ;;
    esac

    return 1
}

reject_private_paths() {
    local context=$1
    shift

    local path
    local -a blocked=()

    for path in "$@"; do
        if is_private_path "$path"; then
            blocked+=("$path")
        fi
    done

    if ((${#blocked[@]} == 0)); then
        return 0
    fi

    printf '\nRefusing to continue: private or generated files are present in %s:\n' "$context" >&2
    for path in "${blocked[@]}"; do
        printf '  - %q\n' "$path" >&2
    done
    printf '\nNo commit was created. Keep these paths ignored and outside the commit.\n' >&2
    printf 'If a path is already staged, inspect '\''git status'\'' and unstage it yourself before rerunning this script.\n' >&2
    return 1
}

collect_pending_paths() {
    local path
    declare -A seen=()

    while IFS= read -r -d '' path; do
        seen["$path"]=1
    done < <(git diff --name-only --no-renames -z)

    while IFS= read -r -d '' path; do
        seen["$path"]=1
    done < <(git diff --cached --name-only --no-renames -z)

    while IFS= read -r -d '' path; do
        seen["$path"]=1
    done < <(git ls-files --others --exclude-standard -z)

    printf '%s\0' "${!seen[@]}"
}

push_current_branch() {
    local commit_hash=$1

    if git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' >/dev/null 2>&1; then
        printf 'Pushing with: git push\n'
        if ! git push; then
            die "push failed. Commit $commit_hash remains local; resolve network, authentication, or remote issues and rerun this script or run 'git push' yourself."
        fi
    else
        printf 'No upstream configured. Pushing with: git push -u origin %s\n' "$branch"
        if ! git push -u origin "$branch"; then
            die "push failed. Commit $commit_hash remains local; resolve network, authentication, or remote issues and rerun this script or run 'git push -u origin $branch' yourself."
        fi
    fi

    printf 'Push completed successfully.\n'
    printf 'Commit %s is now pushed from branch %s.\n' "$commit_hash" "$branch"
}

if [[ ! -t 0 ]]; then
    die "interactive input is required; run this script yourself from a terminal."
fi

git rev-parse --is-inside-work-tree >/dev/null 2>&1 \
    || die "the current directory is not inside a Git working tree."

repo_root=$(git rev-parse --show-toplevel) \
    || die "unable to determine the repository root."
cd "$repo_root"

branch=$(git symbolic-ref --quiet --short HEAD) \
    || die "detached HEAD state detected; check out a branch yourself before committing."

origin_url=$(git remote get-url origin 2>/dev/null) \
    || die "no 'origin' remote exists; configure it yourself before using this script."

git_user_name=$(git config --get user.name 2>/dev/null || true)
git_user_email=$(git config --get user.email 2>/dev/null || true)
if [[ -z "${git_user_name//[[:space:]]/}" || -z "${git_user_email//[[:space:]]/}" ]]; then
    printf '%s: Git author identity is not configured.\n' "$SCRIPT_NAME" >&2
    printf 'Set it yourself for this repository, using your real assessment identity:\n\n' >&2
    printf '  git config --local user.name "Your Name"\n' >&2
    printf '  git config --local user.email "you@example.com"\n\n' >&2
    printf 'Then rerun ./%s. This script will not set or store your identity.\n' "$SCRIPT_NAME" >&2
    exit 1
fi

printf 'Repository root: %s\n' "$repo_root"
printf 'Current branch:  %s\n' "$branch"
printf 'Origin:          %s\n\n' "$origin_url"

status_output=$(git status --short --untracked-files=all)
if [[ -z "$status_output" ]]; then
    if ! commit_hash=$(git rev-parse --verify HEAD 2>/dev/null); then
        printf 'No changes and no commits to push. Nothing was staged, committed, or pushed.\n'
        exit 0
    fi

    if git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' >/dev/null 2>&1; then
        ahead_count=$(git rev-list --count '@{upstream}..HEAD')
        if ((ahead_count == 0)); then
            printf 'No changes to commit and no local commits waiting to be pushed.\n'
            exit 0
        fi
        printf 'No working-tree changes, but %s local commit(s) have not been pushed.\n' "$ahead_count"
        if ! confirm "Push the existing local commit(s) now?"; then
            printf 'Push cancelled. No Git write operation was performed.\n'
            exit 0
        fi
    else
        printf 'No working-tree changes, but branch %s has no available upstream.\n' "$branch"
        if ! confirm "Push commit $commit_hash and set origin/$branch as upstream?"; then
            printf 'Push cancelled. No Git write operation was performed.\n'
            exit 0
        fi
    fi

    push_current_branch "$commit_hash"
    exit 0
fi

printf 'Modified, deleted, staged, and untracked files:\n%s\n' "$status_output"

declare -a pending_paths=()
while IFS= read -r -d '' path; do
    [[ -n "$path" ]] && pending_paths+=("$path")
done < <(collect_pending_paths)

reject_private_paths "the pending change set" "${pending_paths[@]}" \
    || die "remove private paths from the change set and rerun the script."

if ! confirm "Stage all displayed changes with 'git add -A'?"; then
    printf 'Cancelled before staging. No Git write operation was performed.\n'
    exit 0
fi

if ! git add -A; then
    die "staging failed. Inspect 'git status', correct the problem, and rerun the script."
fi

declare -a staged_paths=()
while IFS= read -r -d '' path; do
    [[ -n "$path" ]] && staged_paths+=("$path")
done < <(git diff --cached --name-only --no-renames -z)

if ((${#staged_paths[@]} == 0)); then
    printf 'No staged changes remain after applying .gitignore. Nothing will be committed.\n'
    exit 0
fi

if ! reject_private_paths "the staged change set" "${staged_paths[@]}"; then
    die "private paths were staged. Unstage them yourself, verify 'git status', and rerun the script."
fi

printf '\nStaged change summary:\n'
git diff --cached --stat
printf '\nStaged filenames:\n'
git diff --cached --name-status

if ! git diff --cached --check; then
    die "the staged diff failed Git's whitespace/conflict-marker check. Fix it, restage it yourself, and rerun the script."
fi

commit_message=''
read -r -p "Enter the commit message: " commit_message \
    || die "unable to read a commit message."

if [[ -z "${commit_message//[[:space:]]/}" ]]; then
    die "the commit message cannot be empty or whitespace only."
fi

printf '\nCommit message:\n  %s\n' "$commit_message"
if ! confirm "Create this commit?"; then
    printf 'Cancelled before commit. Changes remain staged; inspect them with '\''git status'\''.\n'
    exit 0
fi

if ! git commit -m "$commit_message"; then
    die "commit failed or a Git hook rejected it. The commit was not bypassed; inspect the hook output and 'git status'."
fi

commit_hash=$(git rev-parse HEAD)
printf '\nCreated commit: %s\n' "$commit_hash"
push_current_branch "$commit_hash"
