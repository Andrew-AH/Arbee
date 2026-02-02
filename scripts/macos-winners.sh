WINNERS="${PWD}/src/jobs/update_winners.py"
VENV_PATH="${PWD}/.venv"

run_in_terminal() {
    local cmd="$1"
    osascript <<EOF
tell application "Terminal"
    do script "cd ${PWD} && source $VENV_PATH/bin/activate && $cmd"
    activate
end tell
EOF
}

run_in_terminal "python3 $WINNERS"
