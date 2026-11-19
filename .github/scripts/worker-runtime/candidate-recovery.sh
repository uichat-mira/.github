#!/usr/bin/env bash
set -euo pipefail

root="${RUNNER_TEMP}/mira-worker"
recovery_root="${root}/recovery"
mkdir -p "$recovery_root"

/usr/bin/curl -fsSL --retry 2 --proto '=https' --tlsv1.2 \
  "https://raw.githubusercontent.com/${TRUSTED_WORKFLOW_REPOSITORY}/${TRUSTED_WORKFLOW_SHA}/.github/scripts/worker-candidate/recovery.py" \
  -o "${root}/trusted-recovery.py"
/usr/bin/curl -fsSL --retry 2 --proto '=https' --tlsv1.2 \
  "https://raw.githubusercontent.com/${TRUSTED_WORKFLOW_REPOSITORY}/${TRUSTED_WORKFLOW_SHA}/.github/scripts/worker-candidate/candidate.py" \
  -o "${root}/trusted-candidate.py"
/usr/bin/curl -fsSL --retry 2 --proto '=https' --tlsv1.2 \
  "https://raw.githubusercontent.com/${TRUSTED_WORKFLOW_REPOSITORY}/${TRUSTED_WORKFLOW_SHA}/.github/scripts/worker-validation/validation.py" \
  -o "${root}/trusted-validation.py"
/usr/bin/curl -fsSL --retry 2 --proto '=https' --tlsv1.2 \
  "https://raw.githubusercontent.com/${TRUSTED_WORKFLOW_REPOSITORY}/${TRUSTED_WORKFLOW_SHA}/.github/scripts/worker-repair/repair.py" \
  -o "${root}/trusted-repair.py"
test -s "${root}/trusted-recovery.py"
test -s "${root}/trusted-candidate.py"
test -s "${root}/trusted-validation.py"
test -s "${root}/trusted-repair.py"

profile_file="${root}/validation-profiles.json"
rm -f "$profile_file"
if test -n "$VALIDATION_PROFILE" && git cat-file -e "${CURRENT_BASE_SHA}:.github/mira-validation-profiles.json" 2>/dev/null; then
  git show "${CURRENT_BASE_SHA}:.github/mira-validation-profiles.json" > "$profile_file"
fi

python3 "${root}/trusted-validation.py" contract \
  --profile-file "$profile_file" \
  --profile "$VALIDATION_PROFILE" \
  --max-tier "$VALIDATION_MAX_TIER" \
  --legacy-command "$VERIFICATION_COMMAND" \
  --output "${root}/validation-contract.json"

validation_contract_sha256="$(jq -r '.contract_sha256' "${root}/validation-contract.json")"
test -n "$validation_contract_sha256"

python3 "${root}/trusted-recovery.py" fingerprint \
  --issue-json "${root}/issue.json" \
  --comments-json "${root}/maintainer-comments.json" \
  --base-branch "$BASE_BRANCH" \
  --verification-command "$VERIFICATION_COMMAND" \
  --validation-profile "$VALIDATION_PROFILE" \
  --validation-max-tier "$VALIDATION_MAX_TIER" \
  --validation-contract-sha256 "$validation_contract_sha256" \
  --output "${root}/contract.json"

current_fingerprint="$(jq -r '.fingerprint' "${root}/contract.json")"
ambiguity_guard="$(jq -r '.ambiguity_guard' "${root}/contract.json")"
{
  echo "contract_fingerprint=$current_fingerprint"
  echo "ambiguity_guard=$ambiguity_guard"
} >> "$GITHUB_OUTPUT"

python3 "${root}/trusted-recovery.py" discover-pointer \
  --comments-json "${root}/issue-comments.json" \
  --repository "$GITHUB_REPOSITORY" \
  --issue-number "$ISSUE_NUMBER" \
  --output "${recovery_root}/discovery.json"

if test "$(jq -r '.invalid_latest_pointer // false' "${recovery_root}/discovery.json")" = "true"; then
  invalid_comment_id="$(jq -r '.invalid_pointer_comment_id' "${recovery_root}/discovery.json")"
  jq -n --arg comment "$invalid_comment_id" \
    '{schema_version:1,mode:"recovery_failed",run_worker:false,reuse_candidate:false,reason:"latest_recovery_pointer_invalid",source_comment_id:$comment}' \
    > "${root}/recovery-state.json"
  echo "mode=recovery_failed" >> "$GITHUB_OUTPUT"
  echo "run_worker=false" >> "$GITHUB_OUTPUT"
  echo "source_run_id=" >> "$GITHUB_OUTPUT"
  exit 0
fi

if test "$(jq -r '.found' "${recovery_root}/discovery.json")" != "true"; then
  jq -n \
    --arg fingerprint "$current_fingerprint" \
    --arg guard "$ambiguity_guard" \
    '{schema_version:1,mode:"fresh",run_worker:true,reuse_candidate:false,reason:"no_prior_candidate",contract_fingerprint:$fingerprint,ambiguity_guard:$guard}' \
    > "${root}/recovery-state.json"
  printf '%s\n' "No prior Recovery Candidate exists for this Issue. Start from the explicit current base." > "${root}/recovery-context.txt"
  {
    echo "mode=fresh"
    echo "run_worker=true"
    echo "source_run_id="
    echo "worker_repair_round=0"
  } >> "$GITHUB_OUTPUT"
  exit 0
fi

jq '.pointer' "${recovery_root}/discovery.json" > "${recovery_root}/pointer.json"
source_run_id="$(jq -r '.run_id' "${recovery_root}/pointer.json")"
candidate_artifact_name="$(jq -r '.candidate_artifact_name // ""' "${recovery_root}/pointer.json")"
verify_artifact_name="$(jq -r '.verification_artifact_name // ""' "${recovery_root}/pointer.json")"
delivery_artifact_name="$(jq -r '.delivery_artifact_name // ""' "${recovery_root}/pointer.json")"
prior_base_sha="$(jq -r '.base_sha' "${recovery_root}/pointer.json")"

{
  echo "source_run_id=$source_run_id"
  echo "source_candidate_artifact_name=$candidate_artifact_name"
  echo "source_verify_artifact_name=$verify_artifact_name"
} >> "$GITHUB_OUTPUT"

if test -z "$candidate_artifact_name"; then
  jq -n --arg run "$source_run_id" \
    '{schema_version:1,mode:"recovery_failed",run_worker:false,reuse_candidate:false,reason:"prior_pointer_missing_candidate_artifact",source_run_id:$run}' \
    > "${root}/recovery-state.json"
  echo "mode=recovery_failed" >> "$GITHUB_OUTPUT"
  echo "run_worker=false" >> "$GITHUB_OUTPUT"
  exit 0
fi

mkdir -p "${recovery_root}/candidate" "${recovery_root}/verify" "${recovery_root}/delivery"
set +e
gh run download "$source_run_id" --repo "$GITHUB_REPOSITORY" \
  --name "$candidate_artifact_name" --dir "${recovery_root}/candidate" \
  >"${recovery_root}/candidate-download.stdout" 2>"${recovery_root}/candidate-download.stderr"
candidate_download_rc="$?"
set -e

if test "$candidate_download_rc" -ne 0 || ! test -s "${recovery_root}/candidate/candidate.json" || ! test -s "${recovery_root}/candidate/candidate.patch"; then
  jq -n \
    --arg run "$source_run_id" \
    --arg artifact "$candidate_artifact_name" \
    '{schema_version:1,mode:"recovery_failed",run_worker:false,reuse_candidate:false,reason:"candidate_artifact_unavailable_or_expired_or_incomplete",source_run_id:$run,candidate_artifact_name:$artifact}' \
    > "${root}/recovery-state.json"
  printf 'Historical Candidate pointer exists for run %s, but Artifact %s is unavailable, expired, or incomplete.\n' "$source_run_id" "$candidate_artifact_name" > "${root}/recovery-context.txt"
  echo "mode=recovery_failed" >> "$GITHUB_OUTPUT"
  echo "run_worker=false" >> "$GITHUB_OUTPUT"
  exit 0
fi

normalize_artifact_digest() {
  local digest="${1:-}"
  if test -z "$digest"; then
    printf '%s' ""
  elif [[ "$digest" =~ ^sha256:[0-9a-f]{64}$ ]]; then
    printf '%s' "$digest"
  elif [[ "$digest" =~ ^[0-9a-f]{64}$ ]]; then
    printf 'sha256:%s' "$digest"
  else
    echo "::error::Invalid Artifact digest format." >&2
    return 2
  fi
}

pointer_artifact_id="$(jq -r '.candidate_artifact_id // ""' "${recovery_root}/pointer.json")"
pointer_artifact_digest="$(normalize_artifact_digest "$(jq -r '.candidate_artifact_digest // ""' "${recovery_root}/pointer.json")")"
set +e
gh api "repos/${GITHUB_REPOSITORY}/actions/runs/${source_run_id}/artifacts?per_page=100" \
  > "${recovery_root}/artifact-list.json" 2> "${recovery_root}/artifact-list.stderr"
artifact_list_rc="$?"
set -e
if test "$artifact_list_rc" -ne 0; then
  jq -n --arg run "$source_run_id" \
    '{schema_version:1,mode:"recovery_failed",run_worker:false,reuse_candidate:false,reason:"candidate_artifact_metadata_unavailable",source_run_id:$run}' \
    > "${root}/recovery-state.json"
  echo "mode=recovery_failed" >> "$GITHUB_OUTPUT"
  echo "run_worker=false" >> "$GITHUB_OUTPUT"
  exit 0
fi
artifact_matches="$(jq -c --arg name "$candidate_artifact_name" '[.artifacts[]? | select(.name == $name)]' "${recovery_root}/artifact-list.json")"
if test "$(jq 'length' <<< "$artifact_matches")" -ne 1; then
  jq -n --arg run "$source_run_id" \
    '{schema_version:1,mode:"recovery_failed",run_worker:false,reuse_candidate:false,reason:"candidate_artifact_identity_ambiguous_or_missing",source_run_id:$run}' \
    > "${root}/recovery-state.json"
  echo "mode=recovery_failed" >> "$GITHUB_OUTPUT"
  echo "run_worker=false" >> "$GITHUB_OUTPUT"
  exit 0
fi
actual_artifact_id="$(jq -r '.[0].id' <<< "$artifact_matches")"
actual_artifact_digest="$(normalize_artifact_digest "$(jq -r '.[0].digest // ""' <<< "$artifact_matches")")"
actual_artifact_expired="$(jq -r '.[0].expired' <<< "$artifact_matches")"
if test "$actual_artifact_id" != "$pointer_artifact_id" || test "$actual_artifact_digest" != "$pointer_artifact_digest" || test "$actual_artifact_expired" != "false"; then
  jq -n --arg run "$source_run_id" \
    '{schema_version:1,mode:"recovery_failed",run_worker:false,reuse_candidate:false,reason:"candidate_artifact_identity_mismatch_or_expired",source_run_id:$run}' \
    > "${root}/recovery-state.json"
  echo "mode=recovery_failed" >> "$GITHUB_OUTPUT"
  echo "run_worker=false" >> "$GITHUB_OUTPUT"
  exit 0
fi

prior_verify_state="$(jq -r '.verification_state // "skipped"' "${recovery_root}/pointer.json")"
if test "$prior_verify_state" = "success" || test "$prior_verify_state" = "failure"; then
  if test -z "$verify_artifact_name"; then
    jq -n --arg run "$source_run_id" \
      '{schema_version:1,mode:"recovery_failed",run_worker:false,reuse_candidate:false,reason:"verification_artifact_pointer_missing",source_run_id:$run}' \
      > "${root}/recovery-state.json"
    echo "mode=recovery_failed" >> "$GITHUB_OUTPUT"
    echo "run_worker=false" >> "$GITHUB_OUTPUT"
    exit 0
  fi
  set +e
  gh run download "$source_run_id" --repo "$GITHUB_REPOSITORY" \
    --name "$verify_artifact_name" --dir "${recovery_root}/verify" \
    >"${recovery_root}/verify-download.stdout" 2>"${recovery_root}/verify-download.stderr"
  verify_download_rc="$?"
  set -e
  if test "$verify_download_rc" -ne 0 || ! test -s "${recovery_root}/verify/verify-run.json"; then
    jq -n --arg run "$source_run_id" --arg artifact "$verify_artifact_name" \
      '{schema_version:1,mode:"recovery_failed",run_worker:false,reuse_candidate:false,reason:"verification_artifact_unavailable_expired_or_incomplete",source_run_id:$run,verification_artifact_name:$artifact}' \
      > "${root}/recovery-state.json"
    echo "mode=recovery_failed" >> "$GITHUB_OUTPUT"
    echo "run_worker=false" >> "$GITHUB_OUTPUT"
    exit 0
  fi
elif test "$prior_verify_state" = "skipped"; then
  if test -n "$verify_artifact_name"; then
    jq -n --arg run "$source_run_id" \
      '{schema_version:1,mode:"recovery_failed",run_worker:false,reuse_candidate:false,reason:"verification_pointer_state_mismatch",source_run_id:$run}' \
      > "${root}/recovery-state.json"
    echo "mode=recovery_failed" >> "$GITHUB_OUTPUT"
    echo "run_worker=false" >> "$GITHUB_OUTPUT"
    exit 0
  fi
else
  jq -n --arg run "$source_run_id" \
    '{schema_version:1,mode:"recovery_failed",run_worker:false,reuse_candidate:false,reason:"verification_pointer_state_invalid",source_run_id:$run}' \
    > "${root}/recovery-state.json"
  echo "mode=recovery_failed" >> "$GITHUB_OUTPUT"
  echo "run_worker=false" >> "$GITHUB_OUTPUT"
  exit 0
fi

prior_delivery_state="$(jq -r '.delivery_state // "skipped"' "${recovery_root}/pointer.json")"
if test "$prior_delivery_state" = "success" || test "$prior_delivery_state" = "failure"; then
  if test -z "$delivery_artifact_name"; then
    jq -n --arg run "$source_run_id" \
      '{schema_version:1,mode:"recovery_failed",run_worker:false,reuse_candidate:false,reason:"delivery_artifact_pointer_missing",source_run_id:$run}' \
      > "${root}/recovery-state.json"
    echo "mode=recovery_failed" >> "$GITHUB_OUTPUT"
    echo "run_worker=false" >> "$GITHUB_OUTPUT"
    exit 0
  fi
  set +e
  gh run download "$source_run_id" --repo "$GITHUB_REPOSITORY" \
    --name "$delivery_artifact_name" --dir "${recovery_root}/delivery" \
    >"${recovery_root}/delivery-download.stdout" 2>"${recovery_root}/delivery-download.stderr"
  delivery_download_rc="$?"
  set -e
  if test "$delivery_download_rc" -ne 0 || ! test -s "${recovery_root}/delivery/delivery-run.json"; then
    jq -n --arg run "$source_run_id" --arg artifact "$delivery_artifact_name" \
      '{schema_version:1,mode:"recovery_failed",run_worker:false,reuse_candidate:false,reason:"delivery_artifact_unavailable_expired_or_incomplete",source_run_id:$run,delivery_artifact_name:$artifact}' \
      > "${root}/recovery-state.json"
    echo "mode=recovery_failed" >> "$GITHUB_OUTPUT"
    echo "run_worker=false" >> "$GITHUB_OUTPUT"
    exit 0
  fi
elif test "$prior_delivery_state" = "skipped"; then
  if test -n "$delivery_artifact_name"; then
    jq -n --arg run "$source_run_id" \
      '{schema_version:1,mode:"recovery_failed",run_worker:false,reuse_candidate:false,reason:"delivery_pointer_state_mismatch",source_run_id:$run}' \
      > "${root}/recovery-state.json"
    echo "mode=recovery_failed" >> "$GITHUB_OUTPUT"
    echo "run_worker=false" >> "$GITHUB_OUTPUT"
    exit 0
  fi
else
  jq -n --arg run "$source_run_id" \
    '{schema_version:1,mode:"recovery_failed",run_worker:false,reuse_candidate:false,reason:"delivery_pointer_state_invalid",source_run_id:$run}' \
    > "${root}/recovery-state.json"
  echo "mode=recovery_failed" >> "$GITHUB_OUTPUT"
  echo "run_worker=false" >> "$GITHUB_OUTPUT"
  exit 0
fi

prior_base_sha="$(jq -r '.base_sha' "${recovery_root}/pointer.json")"
prior_contract_fingerprint="$(jq -r '.contract_fingerprint' "${recovery_root}/pointer.json")"
exact_root="${recovery_root}/exact-base"
set +e
git worktree add --detach "$exact_root" "$prior_base_sha" \
  >"${recovery_root}/worktree.stdout" 2>"${recovery_root}/worktree.stderr"
worktree_rc="$?"
set -e
if test "$worktree_rc" -ne 0; then
  jq -n --arg run "$source_run_id" \
    '{schema_version:1,mode:"recovery_failed",run_worker:false,reuse_candidate:false,reason:"candidate_base_unavailable",source_run_id:$run}' \
    > "${root}/recovery-state.json"
  echo "mode=recovery_failed" >> "$GITHUB_OUTPUT"
  echo "run_worker=false" >> "$GITHUB_OUTPUT"
  exit 0
fi
set +e
python3 "${root}/trusted-candidate.py" restore \
  --repo "$exact_root" \
  --candidate-dir "${recovery_root}/candidate" \
  --expected-repository "$GITHUB_REPOSITORY" \
  --expected-issue-number "$ISSUE_NUMBER" \
  --expected-base-sha "$prior_base_sha" \
  --expected-contract-fingerprint "$prior_contract_fingerprint" \
  >"${recovery_root}/exact-restore.stdout" 2>"${recovery_root}/exact-restore.stderr"
exact_restore_rc="$?"
set -e
git worktree remove --force "$exact_root"
if test "$exact_restore_rc" -ne 0; then
  jq -n --arg run "$source_run_id" \
    '{schema_version:1,mode:"recovery_failed",run_worker:false,reuse_candidate:false,reason:"candidate_exact_restore_failed",source_run_id:$run}' \
    > "${root}/recovery-state.json"
  echo "mode=recovery_failed" >> "$GITHUB_OUTPUT"
  echo "run_worker=false" >> "$GITHUB_OUTPUT"
  exit 0
fi

decision_args=(
  decide
  --current-contract "${root}/contract.json"
  --pointer "${recovery_root}/pointer.json"
  --candidate-manifest "${recovery_root}/candidate/candidate.json"
  --repository "$GITHUB_REPOSITORY"
  --issue-number "$ISSUE_NUMBER"
  --output "${root}/recovery-state.json"
)
if test -s "${recovery_root}/verify/verify-run.json"; then
  decision_args+=(--verify-run "${recovery_root}/verify/verify-run.json")
fi
if test -s "${recovery_root}/delivery/delivery-run.json"; then
  decision_args+=(--delivery-run "${recovery_root}/delivery/delivery-run.json")
fi
python3 "${root}/trusted-recovery.py" "${decision_args[@]}"

mode="$(jq -r '.mode' "${root}/recovery-state.json")"
run_worker="$(jq -r '.run_worker' "${root}/recovery-state.json")"



if test "$mode" = "recoverable"; then
  if test "$prior_base_sha" = "$CURRENT_BASE_SHA"; then
    python3 "${root}/trusted-candidate.py" restore \
      --repo "$GITHUB_WORKSPACE" \
      --candidate-dir "${recovery_root}/candidate" \
      --expected-repository "$GITHUB_REPOSITORY" \
      --expected-issue-number "$ISSUE_NUMBER" \
      --expected-base-sha "$prior_base_sha" \
      --expected-contract-fingerprint "$current_fingerprint" \
      >"${recovery_root}/workspace-restore.json"
    git reset
    jq '.base_strategy="exact_base_restore"' "${root}/recovery-state.json" > "${root}/recovery-state.tmp"
    mv "${root}/recovery-state.tmp" "${root}/recovery-state.json"
  elif git merge-base --is-ancestor "$prior_base_sha" "$CURRENT_BASE_SHA"; then
    set +e
    git apply --3way --index --whitespace=nowarn -- "${recovery_root}/candidate/candidate.patch" \
      >"${recovery_root}/rebase.stdout" 2>"${recovery_root}/rebase.stderr"
    rebase_rc="$?"
    set -e
    if test "$rebase_rc" -eq 0; then
      git reset
      jq '.base_strategy="base_advanced_clean_3way"' "${root}/recovery-state.json" > "${root}/recovery-state.tmp"
      mv "${root}/recovery-state.tmp" "${root}/recovery-state.json"
    else
      git reset --hard "$CURRENT_BASE_SHA"
      git clean -fd
      jq '.mode="recovery_failed" | .run_worker=false | .reuse_candidate=false | .reason="base_advanced_3way_conflict" | .base_strategy="conflict_fail_closed"' \
        "${root}/recovery-state.json" > "${root}/recovery-state.tmp"
      mv "${root}/recovery-state.tmp" "${root}/recovery-state.json"
      mode="recovery_failed"
      run_worker="false"
    fi
  else
    jq '.mode="recovery_failed" | .run_worker=false | .reuse_candidate=false | .reason="candidate_base_diverged_from_current_base" | .base_strategy="diverged_fail_closed"' \
      "${root}/recovery-state.json" > "${root}/recovery-state.tmp"
    mv "${root}/recovery-state.tmp" "${root}/recovery-state.json"
    mode="recovery_failed"
    run_worker="false"
  fi
fi

source_repair_round="$(jq -r '.repair_round // 0' "${root}/recovery-state.json")"
worker_repair_round="$source_repair_round"
validation_result="$(jq -r '.validation_result // ""' "${root}/recovery-state.json")"
if test "$mode" = "recoverable" && test "$validation_result" = "REPAIR"; then
  worker_repair_round="$(jq -r '.next_repair_round // ""' "${root}/recovery-state.json")"
fi
if test "$run_worker" = "true"; then
  case "$worker_repair_round" in
    0|1|2) ;;
    *) echo "::error::Recovery produced an invalid Worker repair round." >&2; exit 1 ;;
  esac
fi

export RECOVERY_STATE_FILE="${root}/recovery-state.json"
export RECOVERY_CONTEXT_FILE="${root}/recovery-context.txt"
export VERIFY_LOG="${recovery_root}/verify/verification.log"

if test "$mode" = "recoverable" && test "$validation_result" = "REPAIR"; then
  if ! test -s "${recovery_root}/verify/validation-report.json"; then
    jq '.mode="recovery_failed" | .run_worker=false | .reuse_candidate=false | .reason="structured_repair_validation_report_missing"' \
      "${root}/recovery-state.json" > "${root}/recovery-state.tmp"
    mv "${root}/recovery-state.tmp" "${root}/recovery-state.json"
    mode="recovery_failed"
    run_worker="false"
  else
    set +e
    python3 "${root}/trusted-repair.py" context \
      --issue-json "${root}/issue.json" \
      --contract-json "${root}/contract.json" \
      --candidate-manifest "${recovery_root}/candidate/candidate.json" \
      --validation-report "${recovery_root}/verify/validation-report.json" \
      --validation-artifact-name "$verify_artifact_name" \
      --repair-round "$worker_repair_round" \
      --output "${root}/repair-context.json" \
      >"${recovery_root}/repair-context.stdout" \
      2>"${recovery_root}/repair-context.stderr"
    repair_context_rc="$?"
    set -e
    if test "$repair_context_rc" -ne 0; then
      jq '.mode="recovery_failed" | .run_worker=false | .reuse_candidate=false | .reason="structured_repair_context_build_failed"' \
        "${root}/recovery-state.json" > "${root}/recovery-state.tmp"
      mv "${root}/recovery-state.tmp" "${root}/recovery-state.json"
      mode="recovery_failed"
      run_worker="false"
    else
      cp "${root}/repair-context.json" "${root}/recovery-context.txt"
    fi
  fi
fi

if ! test -s "${root}/recovery-context.txt"; then
  python3 - <<'PY'
import json, os
from pathlib import Path

state = json.loads(Path(os.environ["RECOVERY_STATE_FILE"]).read_text())
verify_log = Path(os.environ["VERIFY_LOG"])
verification = verify_log.read_text(errors="replace")[:12000] if verify_log.exists() else "(none)"
text = [
    "Mira Candidate Recovery context",
    f"- mode: {state.get('mode')}",
    f"- source run: {state.get('source_run_id')}",
    f"- source base: {state.get('source_base_sha')}",
    f"- reason: {state.get('reason')}",
    f"- base strategy: {state.get('base_strategy', 'none')}",
    "",
    "Trusted prior verification evidence (legacy/unclassified compatibility only):",
    verification,
    "",
    "Rules:",
    "- Existing restored code is prior Candidate work. Inspect and continue it; do not discard it merely to restart.",
    "- Prior Worker narrative is not a trusted PASS.",
    "- Structured REPAIR must use the trusted repair-context contract rather than raw-log interpretation.",
]
Path(os.environ["RECOVERY_CONTEXT_FILE"]).write_text("\n".join(text) + "\n")
PY
fi

{
  echo "mode=$mode"
  echo "run_worker=$run_worker"
  echo "source_run_id=$source_run_id"
  echo "worker_repair_round=$worker_repair_round"
} >> "$GITHUB_OUTPUT"
