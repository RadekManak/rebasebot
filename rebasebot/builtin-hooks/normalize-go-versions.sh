#!/bin/bash
# The script downgrades the go version in all go.mod files to the major.minor.0 format (e.g., 1.24.7 becomes 1.24.0).
# It excludes go.mod files in vendor directories.
# After downgrading the go directive to .0 patch version, it runs `go mod tidy` to increase the version to the minimal version required by the dependencies.
# Finally, it commits the changes to the repository with the message
# "UPSTREAM: <drop>: Normalize go patch version to minimal version required by deps".

set -e
set -o pipefail

stage_and_commit(){
    local commit_message="$1"

    # If committer email and name is passed as environment variable then use it.
    if [[ -z "$REBASEBOT_GIT_USERNAME" || -z "$REBASEBOT_GIT_EMAIL" ]]; then
        author_flag=()
    else
        author_flag=(--author="$REBASEBOT_GIT_USERNAME <$REBASEBOT_GIT_EMAIL>")
    fi

    if [[ -n $(git status --porcelain) ]]; then
        git add -A
        git commit "${author_flag[@]}" -q -m "$commit_message"
    fi
}

normalize_go_mod(){
    local go_mod_file="$1"
    local go_mod_dir
    local current_version
    local major_minor
    local normalized_version

    go_mod_dir=$(dirname "$go_mod_file")

    # Extract the current go version from go.mod
    current_version=$(cd "$go_mod_dir" && go list -m -f '{{.GoVersion}}')

    if [[ -z "$current_version" ]]; then
        echo "no go version found in $go_mod_file" >&2
        return 1
    fi

    # Extract major and minor version (e.g., from 1.24.7, extract 1.24)
    major_minor=$(echo "$current_version" | cut -d. -f1-2)

    # Normalize to major.minor.0 format
    normalized_version="${major_minor}.0"

    # Skip if already in the correct format
    if [[ "$current_version" == "$normalized_version" ]]; then
        return 0
    fi

    echo "Normalizing $go_mod_file: $current_version -> $normalized_version"

    # Update the go version using go mod edit
    (cd "$go_mod_dir" && go mod edit -go="$normalized_version")

    # Increase the version to the minimal version required by the dependencies
    (cd "$go_mod_dir" && go mod tidy)
}

main(){
    local go_mod_files

    # Find all go.mod files excluding vendor directories
    go_mod_files=$(find . -name "go.mod" -type f ! -path "*/vendor/*")

    if [[ -z "$go_mod_files" ]]; then
        echo "no go.mod files found" >&2
        exit 1
    fi

    # Process each go.mod file
    while IFS= read -r go_mod_file; do
        normalize_go_mod "$go_mod_file"
    done <<< "$go_mod_files"

    # Stage and commit all changes together
    stage_and_commit "UPSTREAM: <drop>: Downgrade go version"
}

main
