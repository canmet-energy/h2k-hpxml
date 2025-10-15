#!/bin/bash
###############################################################################
# dev-env-init.sh
# Unified DevContainer shell initializer (idempotent, re-source safe).
#
# Features
#   * Auto-create & activate project virtualenv (first source only)
#   * Informative prompt: exit code, venv, user, path, git branch (+ dirty)
#   * Bright color palette (configurable) with graceful fallback if term limited
#   * Fast: only git + path segments are dynamic; everything else cached
#   * Safe to re-source: functions always refreshed, bootstrap only once
#
# Simplicity principle: no runtime knobs; always bright, classic multi-line prompt.
#
# Exit quietly in non-interactive shells to avoid overhead in scripts.
###############################################################################

case $- in *i*) : ;; *) return 0 2>/dev/null || exit 0 ;; esac

## ---------------------------------------------------------------------------
## One‑time bootstrap guard
##   - We only create/activate the venv on the first load
##   - Functions & prompt logic ALWAYS refresh so edits take effect immediately
## ---------------------------------------------------------------------------
if [ -z "${DEV_ENV_INIT_DONE:-}" ]; then
  DEV_ENV_INIT_DONE=1   # (intentionally not exported to child shells)
  _DEV_ENV_DO_BOOTSTRAP=1
else
  _DEV_ENV_DO_BOOTSTRAP=0
fi

WORKSPACE="${containerWorkspaceFolder:-/workspaces/bluesky}"
VENV_PATH="$WORKSPACE/.venv"

## Virtualenv bootstrap (first load only)
if [ "$_DEV_ENV_DO_BOOTSTRAP" = "1" ] && [ -z "${VIRTUAL_ENV:-}" ]; then
  if [ ! -f "$VENV_PATH/bin/activate" ] && command -v python3 >/dev/null 2>&1; then
    python3 -m venv "$VENV_PATH" >/dev/null 2>&1 || true
  fi
  # shellcheck disable=SC1091
  [ -f "$VENV_PATH/bin/activate" ] && . "$VENV_PATH/bin/activate" >/dev/null 2>&1 || true
fi

## Color palette assembly ----------------------------------------------------
_dev_init_colors() {
  if command -v tput >/dev/null 2>&1; then
    C_RESET="$(tput sgr0)"; C_DIM="$(tput setaf 8)"; C_BOLD="$(tput bold)";
    # Base colors first
    C_RED="$(tput setaf 1)"; C_GREEN="$(tput setaf 2)"; C_YELLOW="$(tput setaf 3)"; C_BLUE="$(tput setaf 4)"; C_MAGENTA="$(tput setaf 5)"; C_CYAN="$(tput setaf 6)";
    # Try to upgrade to bright palette if terminal supports extended setaf codes
    if tput setaf 9 >/dev/null 2>&1; then
      C_RED="$(tput setaf 9)"; C_GREEN="$(tput setaf 10)"; C_BLUE="$(tput setaf 12)";
      tput setaf 13 >/dev/null 2>&1 && C_MAGENTA="$(tput setaf 13)"
      tput setaf 14 >/dev/null 2>&1 && C_CYAN="$(tput setaf 14)"
    fi
  else
    # ANSI fallback (already bright variants)
    C_RESET='\e[0m'; C_DIM='\e[2m'; C_BOLD='\e[1m';
    C_RED='\e[91m'; C_GREEN='\e[92m'; C_YELLOW='\e[33m'; C_BLUE='\e[94m'; C_MAGENTA='\e[95m'; C_CYAN='\e[96m'
  fi
}
_dev_init_colors


_dev_git_segment() {   # Git branch (red when dirty, magenta when clean)
  command -v git >/dev/null 2>&1 || return 0
  local branch dirty color
  branch=$(git symbolic-ref --quiet --short HEAD 2>/dev/null || git describe --tags --always 2>/dev/null) || return 0
  if git diff --no-ext-diff --quiet 2>/dev/null && git diff --no-ext-diff --cached --quiet 2>/dev/null; then
    dirty=""; color="$C_MAGENTA"
  else
    dirty="*"; color="$C_RED"
  fi
  printf '%s(%s%s)%s' "${color:-$C_MAGENTA}" "$branch" "$dirty" "$C_RESET"
}

_dev_path_segment() {  # Current path with ~ substitution
  printf '%s%s%s' "$C_BLUE" "${PWD/#$HOME/~}" "$C_RESET"
}

_dev_venv_segment() {  # Active virtualenv name (if any)
  [ -z "${VIRTUAL_ENV:-}" ] && return 0
  local name=$(basename "$VIRTUAL_ENV")
  [ "$name" = ".venv" ] && name="venv"
  printf '%s(%s)%s ' "$C_CYAN" "$name" "$C_RESET"
}

_dev_exit_segment() {  # Red ✘ when previous command failed
  [ "$1" -ne 0 ] && printf '%s✘%s ' "$C_RED" "$C_RESET"
}

_dev_user_segment() {  # Username only (keeps prompt compact)
  printf '%s%s%s' "$C_GREEN" "${USER:-user}" "$C_RESET"
}

_dev_gpu_segment() {  # Show GPU icon if NVIDIA runtime present (cached)
  if [ -n "${DEV_GPU_ICON_CACHED:-}" ]; then
    [ -n "$DEV_GPU_ICON_CACHED" ] && printf '%s' "$DEV_GPU_ICON_CACHED"
    return 0
  fi
  if command -v nvidia-smi >/dev/null 2>&1; then
    # Simple assumption: if nvidia-smi exists, GPU accessible; choose universal icon
    DEV_GPU_ICON_CACHED='⚡'
    printf '%s' "$DEV_GPU_ICON_CACHED"
  else
    DEV_GPU_ICON_CACHED=''
  fi
}

_dev_build_ps1() {     # Classic multi-line prompt only
  local ec=$? arrow="${C_DIM}➜${C_RESET}" git path venv user exitc gpu
  exitc=$(_dev_exit_segment $ec)
  venv=$(_dev_venv_segment)
  user=$(_dev_user_segment)
  path=$(_dev_path_segment)
  git=$(_dev_git_segment)
  gpu=$(_dev_gpu_segment)
  PS1="${exitc}${venv}${user} ${arrow} ${path} ${git}${gpu:+ $gpu}\n$ "
}

## Hook into PROMPT_COMMAND (prepend once)
if [ -n "${PROMPT_COMMAND:-}" ]; then
  case "$PROMPT_COMMAND" in *"_dev_build_ps1"*) : ;; *) PROMPT_COMMAND="_dev_build_ps1; $PROMPT_COMMAND" ;; esac
else
  PROMPT_COMMAND="_dev_build_ps1"
fi
export PROMPT_COMMAND

return 0 2>/dev/null || true  # (Allows 'source' in bash -c contexts without error)