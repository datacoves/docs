#!/bin/bash
export PS1="\[\033[1;36m\]\w \[\033[0m\]\$ "

export PATH=/config/.local/bin:$PATH

source /usr/share/bash-completion/completions/git

alias code=code-server


if [[ -f "/config/.bash_custom" ]]; then
    source "/config/.bash_custom"
fi

