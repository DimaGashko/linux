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