import test from "node:test";
import assert from "node:assert/strict";
import { createHash, createHmac } from "node:crypto";
import { createBatch, sendBatch, signBatch } from "./reporter.mjs";

const run = 44109926833;
const issue = 2;
const artifactId = 14000000001;
function fixture(overrides = {}) {
  const needs = {
    worker_capture: { result: "success", outputs: {
      candidate_artifact_id: String(artifactId),
      candidate_artifact_name: "candidate-2-44109926833-1",
      recovery_mode: "none",
    }},
    verify: { result: "success", outputs: { verification_artifact_name: "verify-2-44109926833-1" } },
    delivery: { result: "success", outputs: { pull_request_url: "https://github.com/uichat-mira/how-am-i/pull/5" } },
    recovery_index: { result: "success", outputs: {} },
  };
  const jobs = ["worker_capture", "verify", "delivery", "recovery_index"].map((name) => ({
    name: "worker / " + name,
    status: "completed",
    conclusion: "success",
  }));
  const artifacts = [
    { id: artifactId, name: "candidate-2-44109926833-1", expired: false },
    { id: 14000000002, name: "verify-2-44109926833-1", expired: false },
  ];
  return {
    repository: "uichat-mira/how-am-i", issue, runId: String(run), attempt: 1,
    needs, jobs, artifacts, deliveryPrNumber: 5,
    ...overrides,
  };
}


function repairFixture({ escalated = false } = {}) {
  const f = fixture();
  const repair1Id = 14000000003;
  const repair2Id = 14000000004;
  f.needs.initial_repair_outcome = { result: "success", outputs: { state: "RETURNED", next_repair_round: "1" } };
  f.needs.repair_round_1 = {
    result: "success",
    outputs: escalated
      ? {
          state: "RETURNED",
          repair_round: "1",
          next_repair_round: "2",
          candidate_artifact_id: String(repair1Id),
          candidate_artifact_name: "candidate-r1",
          verification_artifact_name: "verify-r1",
          validation_result: "REPAIR",
          verification_terminal_status: "failure",
        }
      : {
          state: "VERIFIED",
          repair_round: "1",
          candidate_artifact_id: String(repair1Id),
          candidate_artifact_name: "candidate-r1",
          verification_artifact_name: "verify-r1",
          validation_result: "PASS",
          verification_terminal_status: "success",
        },
  };
  f.needs.repair_round_2 = escalated
    ? {
        result: "success",
        outputs: {
          state: "ESCALATED",
          repair_round: "2",
          candidate_artifact_id: String(repair2Id),
          candidate_artifact_name: "candidate-r2",
          verification_artifact_name: "verify-r2",
          validation_result: "REPAIR",
          verification_terminal_status: "failure",
        },
      }
    : { result: "skipped", outputs: {} };
  f.needs.lifecycle_handoff = {
    result: "success",
    outputs: escalated
      ? {
          state: "ESCALATED",
          repair_round: "2",
          candidate_artifact_id: String(repair2Id),
          candidate_artifact_name: "candidate-r2",
          verification_artifact_name: "verify-r2",
          validation_result: "REPAIR",
          verification_terminal_status: "failure",
        }
      : {
          state: "VERIFIED",
          repair_round: "1",
          candidate_artifact_id: String(repair1Id),
          candidate_artifact_name: "candidate-r1",
          verification_artifact_name: "verify-r1",
          validation_result: "PASS",
          verification_terminal_status: "success",
        },
  };
  if (escalated) {
    f.needs.delivery = { result: "skipped", outputs: {} };
    f.deliveryPrNumber = null;
  }
  f.jobs.push({
    name: "worker / lifecycle_handoff",
    status: "completed",
    conclusion: "success",
  });
  f.artifacts.push(
    { id: repair1Id, name: "candidate-r1", expired: false },
    { id: 14000000005, name: "verify-r1", expired: false },
  );
  if (escalated) {
    f.artifacts.push(
      { id: repair2Id, name: "candidate-r2", expired: false },
      { id: 14000000006, name: "verify-r2", expired: false },
    );
    const deliveryJob = f.jobs.find((job) => job.name.endsWith("/ delivery"));
    deliveryJob.conclusion = "skipped";
  }
  return f;
}

test("emits supported trusted stage events only with matching GitHub evidence", () => {
  const batch = createBatch(fixture());
  assert.equal(batch.schema, "haomai.telemetry.v1");
  assert.deepEqual(batch.events.map((e) => e.kind), [
    "worker.stopped", "candidate.captured", "verify.passed",
    "delivery.draft_pr_created", "run.finished",
  ]);
  assert.equal(batch.events.at(-1).outcome, "success");
  assert.equal(batch.events[1].evidence_ref.id, String(artifactId));
  assert.ok(batch.events.every((e) => e.run_id === String(run) && e.issue_number === issue));
});

test("does not report verified or complete without Verify artifact", () => {
  const f = fixture();
  f.artifacts = f.artifacts.slice(0, 1);
  const batch = createBatch(f);
  assert.ok(!batch.events.some((e) => e.kind === "verify.passed"));
  assert.equal(batch.events.at(-1).outcome, "partial");
  assert.equal(batch.events.at(-1).error_code, "STAGE_EVIDENCE_UNAVAILABLE");
});

test("does not trust mismatched needs and GitHub job conclusion", () => {
  const f = fixture();
  f.jobs[0].conclusion = "failure";
  const batch = createBatch(f);
  assert.ok(!batch.events.some((e) => e.kind === "worker.stopped"));
  assert.equal(batch.events.at(-1).outcome, "partial");
});

test("failed capture with durable Candidate is reported as failure, not PASS", () => {
  const f = fixture();
  f.needs.worker_capture.result = "failure";
  f.jobs[0].conclusion = "failure";
  f.needs.verify.result = "skipped";
  f.jobs[1].conclusion = "skipped";
  f.needs.delivery.result = "skipped";
  f.jobs[2].conclusion = "skipped";
  f.deliveryPrNumber = null;
  const batch = createBatch(f);
  assert.ok(batch.events.some((e) => e.kind === "worker.failed"));
  assert.ok(batch.events.some((e) => e.kind === "candidate.captured"));
  assert.ok(!batch.events.some((e) => e.kind === "verify.passed"));
  assert.equal(batch.events.at(-1).outcome, "failure");
});


test("repair-aware Reporter projects returned round and only final trusted PASS", () => {
  const batch = createBatch(repairFixture());
  const kinds = batch.events.map((e) => e.kind);
  assert.equal(kinds.filter((kind) => kind === "verify.passed").length, 1);
  assert.ok(batch.events.some((e) =>
    e.kind === "recovery.detected" &&
    e.stage === "repair" &&
    e.outcome === "returned" &&
    e.error_code === "VALIDATION_REPAIR_ROUND_1"
  ));
  const candidate = batch.events.find((e) => e.kind === "candidate.captured");
  assert.equal(candidate.evidence_ref.id, "14000000003");
  assert.equal(batch.events.at(-1).outcome, "success");
});

test("cross-run recovered REPAIR reports the actual remaining round", () => {
  const f = repairFixture();
  f.needs.initial_repair_outcome.outputs.next_repair_round = "2";
  f.needs.repair_round_1.outputs.repair_round = "2";
  f.needs.lifecycle_handoff.outputs.repair_round = "2";
  const batch = createBatch(f);
  const returned = batch.events.filter((e) =>
    e.kind === "recovery.detected" && e.stage === "repair" && e.outcome === "returned"
  );
  assert.equal(returned.length, 1);
  assert.equal(returned[0].error_code, "VALIDATION_REPAIR_ROUND_2");
  assert.ok(!batch.events.some((e) => e.error_code === "VALIDATION_REPAIR_ROUND_1"));
});

test("two failed repair rounds project escalation and never fake verify PASS", () => {
  const batch = createBatch(repairFixture({ escalated: true }));
  assert.ok(!batch.events.some((e) => e.kind === "verify.passed"));
  assert.equal(
    batch.events.filter((e) => e.kind === "recovery.detected" && e.stage === "repair").length,
    2,
  );
  assert.ok(batch.events.some((e) =>
    e.kind === "recovery.failed" &&
    e.stage === "repair" &&
    e.outcome === "escalated" &&
    e.error_code === "REPAIR_ROUND_LIMIT_EXHAUSTED"
  ));
  assert.equal(batch.events.at(-1).outcome, "failure");
});

test("initial Verify job success with structured non-PASS does not become verify.passed", () => {
  const f = repairFixture();
  f.needs.lifecycle_handoff.outputs.state = "BLOCKED";
  f.needs.lifecycle_handoff.outputs.validation_result = "BLOCKED";
  f.needs.lifecycle_handoff.outputs.verification_terminal_status = "failure";
  f.needs.delivery = { result: "skipped", outputs: {} };
  f.deliveryPrNumber = null;
  const deliveryJob = f.jobs.find((job) => job.name.endsWith("/ delivery"));
  deliveryJob.conclusion = "skipped";
  const batch = createBatch(f);
  assert.ok(!batch.events.some((e) => e.kind === "verify.passed"));
  assert.ok(batch.events.some((e) =>
    e.kind === "recovery.failed" && e.stage === "repair" && e.outcome === "blocked"
  ));
  assert.equal(batch.events.at(-1).outcome, "failure");
});

test("signed raw bytes match canonical HMAC and never include secret in payload", () => {
  const secret = "x".repeat(48);
  const body = Buffer.from('{"schema":"haomai.telemetry.v1"}');
  const headers = signBatch(body, secret, 1794912000000, "unit-test-nonce-0123456789");
  const bodyHash = createHash("sha256").update(body).digest("hex");
  const expected = createHmac("sha256", secret)
    .update("v1\nPOST\n/v1/events\n1794912000\nunit-test-nonce-0123456789\n" + bodyHash)
    .digest("hex");
  assert.equal(headers["x-haomai-signature"], expected);
  assert.equal(headers["x-haomai-app-id"], "mira-worker-reporter");
  assert.ok(!body.toString().includes(secret));
});

test("HTTP 202 is accepted telemetry, not persistence proof", async () => {
  const batch = createBatch(fixture());
  let calls = 0;
  await sendBatch(batch, "z".repeat(48), async (url, init) => {
    calls++;
    assert.equal(url, "https://how-am-i.dangjingtao.workers.dev/v1/events");
    assert.equal(init.method, "POST");
    assert.equal(init.headers["x-haomai-app-id"], "mira-worker-reporter");
    return { status: 202, json: async () => ({ accepted: true, event_count: batch.events.length, persisted: false }) };
  });
  assert.equal(calls, 1);
  await assert.rejects(() => sendBatch(batch, "z".repeat(48), async () => ({
    status: 202, json: async () => ({ accepted: false }),
  })), /Unexpected collector acceptance/);
});

test("invalid repository identity cannot reach HMAC transport", () => {
  assert.throws(() => createBatch(fixture({ repository: "other-org/evil" })), /Unexpected organization/);
  assert.throws(() => createBatch(fixture({ issue: 0 })), /Invalid Issue/);
});
