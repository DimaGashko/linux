GREEN="\[$(tput setaf 2)\]"
RESET="\[$(tput sgr0)\]"

[[ $- != *i* ]] && return

source /usr/share/doc/pkgfile/command-not-found.bash
source /usr/share/nvm/init-nvm.sh
source ~/config/bash/.bashrc_tmp.sh

parseGitBranch() {
  git branch 2>/dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/(\1)/'
}

formatGitBranch() {
  branch=$(parseGitBranch)
  if [ "$branch" == "(master)" ] || [ "$branch" == "(main)" ]; then
    echo ${branch^^}
  else
    echo $branch
  fi
}

PS1="\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w \[\e[91m\]\$(formatGitBranch)\[\e[00m\]$ "

PS2="${GREEN}>${RESET} "

shopt -s checkwinsize
shopt -s histappend
shopt -s globstar
shopt -s autocd

HISTCONTROL=ignoreboth
HISTFILESIZE=10000
HISTSIZE=1000

alias @='source ~/.bashrc'

alias grep='grep --color=auto'
alias ls='ls --color=auto'
alias ll='ls -Al'
alias la='ls -A'
alias l='ls -C'
alias tree='tree -C'

alias cwd='pwd | xclip -sel clipboard'

export GCC_COLORS='error=01;31:warning=01;35:note=01;36:caret=01;32:locus=01:quote=01'
export john=/usr/share/ptools/john/run

export EDITOR=vim
export VISUAL=vim
export QT_QPA_PLATFORMTHEME=qt5ct
