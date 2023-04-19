[[ $- != *i* ]] && return

# Suggests a package to install if a command is not found
source /usr/share/doc/pkgfile/command-not-found.bash
source /usr/share/nvm/init-nvm.sh

for f in ~/config/bash/bashrc.d/*; do
  source $f
done

shopt -s checkwinsize
shopt -s histappend
shopt -s globstar

HISTCONTROL=ignoreboth
HISTFILESIZE=10000
HISTSIZE=1000

alias @='source ~/.bashrc'

alias grep='grep --color=auto'
alias ls='lsd'
alias lt='lsd --tree'
alias tree='tree -C'

cd() {
  builtin cd "$@"

  l=`ls | wc -l`
  if (( $l < 30 )); then
    ls
  fi
}

alias copy='xclip -sel clipboard'
alias pac='sudo pacman'

alias mirrors_sync='sudo reflector -c UA,FR,DE,PL,CZ,EE,FI,IT,LT,LV --sort rate --latest 50 --threads 50 --protocol https --verbose --save /etc/pacman.d/mirrorlist'

PS1="\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w \[\e[91m\]\$(formatGitBranch) \[\e[00m\]$ "
PS2="$(tput setaf 2)>$(tput sgr0) "

export SUDO_PROMPT="$(tput bold setab 1 setaf 7)[sudo]$(tput sgr0) $(tput setaf 6)password for$(tput sgr0) $(tput setaf 2)%p$(tput sgr0): "

export GCC_COLORS='error=01;31:warning=01;35:note=01;36:caret=01;32:locus=01:quote=01'

export EDITOR=vim
export VISUAL=vim
export QT_QPA_PLATFORMTHEME=qt5ct

export PATH=$PATH:~/go/bin

export PKG_CONFIG_PATH=/usr/local/lib/pkgconfig/
