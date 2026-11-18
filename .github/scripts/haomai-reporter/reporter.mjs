import { createHash, createHmac, randomBytes, randomUUID } from "node:crypto";

const INGEST_URL = "https://how-am-i.dangjingtao.workers.dev/v1/events";
const STAGES = ["worker_capture", "verify", "delivery", "recovery_index"];
const allowedConclusion = new Set(["success", "failure", "cancelled", "skipped", "timed_out", "action_required"]);

function requirePositiveInt(value, label) {
  const n = Number(value);
  if (!Number.isSafeInteger(n) || n < 1) throw new Error("Invalid " + label);
  return n;
}

function requireIdentity(input) {
  const repository = input.repository;
  if (typeof repository !== "string" || !/^uichat-mira\/[A-Za-z0-9_.-]+$/.test(repository)) {
    throw new Error("Unexpected organization or repository");
  }
  return {
    repository,
    issue: requirePositiveInt(input.issue, "Issue"),
    runId: String(requirePositiveInt(input.runId, "Run ID")),
    attempt: requirePositiveInt(input.attempt, "run attempt"),
  };
}

function matchingJob(allJobs, stage) {
  const matches = allJobs.filter((job) => job.name?.split("/").at(-1)?.trim() === stage);
  return matches.length === 1 && matches[0].status === "completed" ? matches[0] : null;
}

function observedConclusion(needs, jobs, stage) {
  const expected = needs?.[stage]?.result;
  const job = matchingJob(jobs, stage);
  if (!job || !allowedConclusion.has(job.conclusion) || expected !== job.conclusion) return null;
  return job.conclusion;
}

function evidenceArtifact(artifacts, name, id) {
  if (typeof name !== "string" || !/^[A-Za-z0-9_.-]{1,180}$/.test(name)) return null;
  const matches = artifacts.filter((a) => String(a.id) === String(id) && a.name === name && !a.expired);
  return matches.length === 1 ? matches[0] : null;
}

function artifactByName(artifacts, name) {
  return typeof name === "string" && name.length > 0 &&
    artifacts.some((a) => a.name === name && !a.expired);
}

function reportedEvent(id, kind, stage, outcome, level, evidence, errorCode) {
  return {
    event_id: randomUUID(),
    occurred_at: new Date().toISOString(),
    kind,
    level,
    repository: id.repository,
    issue_number: id.issue,
    run_id: id.runId,
    run_attempt: id.attempt,
    stage,
    outcome,
    evidence_ref: evidence,
    ...(errorCode ? { error_code: errorCode } : {}),
  };
}

function runEvidence(id) {
  return { type: "actions-run", id: id.runId };
}

export function createBatch(input) {
  const id = requireIdentity(input);
  const { needs, jobs, artifacts } = input;
  if (!needs || !Array.isArray(jobs) || !Array.isArray(artifacts)) {
    throw new Error("Missing trusted GitHub Jobs or Artifacts evidence");
  }
  const result = (stage) => observedConclusion(needs, jobs, stage);
  const workerResult = result("worker_capture");
  const verifyResult = result("verify");
  const deliveryResult = result("delivery");
  const recoveryResult = result("recovery_index");
  const outputs = needs.worker_capture?.outputs || {};
  const verifyOutputs = needs.verify?.outputs || {};
  const deliveryOutputs = needs.delivery?.outputs || {};
  const recoveryMode = outputs.recovery_mode || "";
  const events = [];
  const add = (kind, stage, outcome, level = "info", evidence = runEvidence(id), code) => {
    events.push(reportedEvent(id, kind, stage, outcome, level, evidence, code));
  };

  if (workerResult === "success") add("worker.stopped", "capture", "success");
  if (workerResult === "failure" || workerResult === "timed_out") {
    add("worker.failed", "capture", "failure", "error", runEvidence(id), "WORKER_JOB_FAILED");
  }

  const candidate = evidenceArtifact(artifacts, outputs.candidate_artifact_name, outputs.candidate_artifact_id);
  if (candidate) {
    add("candidate.captured", "capture", "captured", "info", {
      type: "artifact",
      id: String(candidate.id),
    });
  } else if (workerResult === "success") {
    add("candidate.unavailable", "capture", "unavailable", "warn", runEvidence(id), "CANDIDATE_EVIDENCE_MISSING");
  }

  let verifyEvidence = false;
  if (verifyResult === "success") {
    verifyEvidence = artifactByName(artifacts, verifyOutputs.verification_artifact_name);
    if (verifyEvidence) add("verify.passed", "verify", "success");
  } else if (verifyResult === "failure" || verifyResult === "timed_out") {
    add("verify.failed", "verify", "failure", "error", runEvidence(id), "VERIFY_JOB_FAILED");
  }

  let deliveryEvidence = false;
  const prNumber = input.deliveryPrNumber;
  if (deliveryResult === "success" && Number.isSafeInteger(prNumber) && prNumber > 0) {
    deliveryEvidence = true;
    add("delivery.draft_pr_created", "delivery", "success", "info", {
      type: "pull-request",
      id: String(prNumber),
    });
  } else if (deliveryResult === "failure" || deliveryResult === "timed_out") {
    add("delivery.failed", "delivery", "failure", "error", runEvidence(id), "DELIVERY_JOB_FAILED");
  }

  if (recoveryResult === "failure" || recoveryResult === "timed_out") {
    add("recovery.failed", "recovery", "failure", "warn", runEvidence(id), "RECOVERY_INDEX_FAILED");
  } else if (workerResult === "success" &&
      (recoveryMode === "delivery_retry_only" || recoveryMode === "delivery_complete")) {
    add("recovery.detected", "recovery", "detected");
  }

  const recoveredVerify = recoveryMode === "delivery_retry_only" &&
    outputs.recovered_verify_upload_outcome === "success" &&
    artifactByName(artifacts, outputs.verification_artifact_name);
  const verified = verifyEvidence || recoveredVerify;
  const successfulDelivery = workerResult === "success" && deliveryEvidence && candidate &&
    (verified || recoveryMode === "delivery_complete");
  const alreadyDelivered = recoveryMode === "delivery_complete" && workerResult === "success" &&
    Number.isSafeInteger(prNumber) && prNumber > 0;
  const failed = [workerResult, verifyResult, deliveryResult, recoveryResult]
    .some((s) => s === "failure" || s === "timed_out");
  let overall = "partial";
  if (successfulDelivery || alreadyDelivered) overall = "success";
  else if (failed) overall = "failure";
  add("run.finished", "run", overall,
    overall === "success" ? "info" : overall === "failure" ? "error" : "warn",
    runEvidence(id), overall === "partial" ? "STAGE_EVIDENCE_UNAVAILABLE" : undefined);

  if (events.length > 16) throw new Error("Stage event limit exceeded");
  return { schema: "haomai.telemetry.v1", batch_id: randomUUID(), events };
}

function trustedDeliveryPrNumber(needs, repository) {
  const url = needs.delivery?.outputs?.pull_request_url ||
    (needs.worker_capture?.outputs?.recovery_mode === "delivery_complete"
      ? needs.worker_capture.outputs.pull_request_url : "");
  if (typeof url !== "string") return null;
  const prefix = "https://github.com/" + repository + "/pull/";
  if (!url.startsWith(prefix)) return null;
  const suffix = url.slice(prefix.length);
  return /^[1-9][0-9]*$/.test(suffix) ? Number(suffix) : null;
}

async function githubJson(path, token) {
  const response = await fetch("https://api.github.com/" + path, {
    headers: {
      accept: "application/vnd.github+json",
      authorization: "Bearer " + token,
      "x-github-api-version": "2022-11-28",
      "user-agent": "mira-trusted-reporter-v1",
    },
    signal: AbortSignal.timeout(12000),
  });
  if (!response.ok) throw new Error("GitHub evidence HTTP " + response.status);
  return response.json();
}

export async function collectFacts(identity, token, needs) {
  const id = requireIdentity(identity);
  const path = "repos/" + id.repository + "/actions/runs/" + id.runId;
  const [jobPage, artifactPage] = await Promise.all([
    githubJson(path + "/attempts/" + id.attempt + "/jobs?per_page=100", token),
    githubJson(path + "/artifacts?per_page=100", token),
  ]);
  if (!Array.isArray(jobPage.jobs) || !Array.isArray(artifactPage.artifacts)) {
    throw new Error("Malformed GitHub Jobs or Artifacts response");
  }
  if (jobPage.total_count > jobPage.jobs.length ||
      artifactPage.total_count > artifactPage.artifacts.length) {
    throw new Error("Pagination required; cannot infer unlisted stage evidence");
  }

  let deliveryPrNumber = null;
  const number = trustedDeliveryPrNumber(needs, id.repository);
  if (number !== null) {
    const pr = await githubJson("repos/" + id.repository + "/pulls/" + number, token);
    if (pr.number === number && pr.base?.repo?.full_name === id.repository &&
        pr.base?.ref && (pr.state === "open" || pr.state === "closed")) {
      deliveryPrNumber = number;
    }
  }
  return { ...id, needs, jobs: jobPage.jobs, artifacts: artifactPage.artifacts, deliveryPrNumber };
}

export function signBatch(rawBody, secret, now = Date.now(), nonce = randomBytes(18).toString("base64url")) {
  if (typeof secret !== "string" || secret.length < 32) throw new Error("Reporter signing secret missing or too short");
  const stamp = String(Math.floor(now / 1000));
  const bodyHash = createHash("sha256").update(rawBody).digest("hex");
  const toSign = ["v1", "POST", "/v1/events", stamp, nonce, bodyHash].join("\n");
  return {
    "content-type": "application/json",
    "x-haomai-app-id": "mira-worker-reporter",
    "x-haomai-timestamp": stamp,
    "x-haomai-nonce": nonce,
    "x-haomai-signature": createHmac("sha256", secret).update(toSign).digest("hex"),
  };
}

export async function sendBatch(batch, secret, http = fetch) {
  const raw = Buffer.from(JSON.stringify(batch));
  if (raw.length > 32768) throw new Error("Reporter payload larger than protocol limit");
  for (let attempt = 1; attempt <= 2; attempt++) {
    const response = await http(INGEST_URL, {
      method: "POST",
      headers: signBatch(raw, secret),
      body: raw,
      signal: AbortSignal.timeout(12000),
    });
    if (response.status === 202) {
      const data = await response.json();
      if (data.accepted === true && data.event_count === batch.events.length) return;
      throw new Error("Unexpected collector acceptance response");
    }
    if (attempt < 2 && (response.status === 429 || response.status >= 500)) continue;
    throw new Error("Collector HTTP " + response.status);
  }
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  const secret = process.env.HAOMAI_REPORTER_HMAC_SECRET;
  if (!token) throw new Error("Reporter GitHub token not configured");
  if (!secret || secret.length < 32) throw new Error("Reporter HMAC secret unavailable");
  const needs = JSON.parse(process.env.REPORTER_NEEDS_JSON || "{}");
  const identity = {
    repository: process.env.GITHUB_REPOSITORY,
    issue: process.env.REPORTER_ISSUE_NUMBER,
    runId: process.env.GITHUB_RUN_ID,
    attempt: process.env.GITHUB_RUN_ATTEMPT,
  };
  const facts = await collectFacts(identity, token, needs);
  const batch = createBatch(facts);
  await sendBatch(batch, secret);
  console.log("Trusted Reporter accepted " + batch.events.length + " bounded stage facts for run " +
    facts.runId + "/" + facts.attempt + ". This is telemetry, not verified persistence.");
}

if (process.argv[1] && import.meta.url === new URL("file://" + process.argv[1]).href) {
  main().catch((error) => {
    // Never echo headers, payload, tokens, signing material, or untrusted provider output.
    console.error("Trusted Reporter unavailable: " + (error instanceof Error ? error.message : "unknown"));
    process.exitCode = 1;
  });
}
