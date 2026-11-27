'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { evaluateDeliveryEligibility } = require('../strict_gated_visibility_guard_e085_v1');

const root = path.resolve(__dirname, '../..');
const readJson = p => JSON.parse(fs.readFileSync(path.join(root, p), 'utf8'));
const sha = c => String(c).repeat(64);

function readyFixture() {
  const readyFile = 'research/weekly_purchase/1252/SYNTHETIC_READY_FIXTURE_METADATA_ONLY.json';
  const dataSha = sha('a');
  const codeSha = sha('b');
  const linesSha = sha('c');
  const sealSha = sha('d');
  const gate = {
    status: 'STRICT_PASS_READY', target_round: 1252, data_cutoff: 1251, data_sha256: dataSha,
    strict_model_validation_pass: true, strict_portfolio_pass: true, strict_pass_ready: true,
    ready_file: readyFile, ready_file_exists: true, final_purchase_freeze_allowed: true,
    strict_gate_version: 'UNCHANGED_V1', strict_gate_evaluation: 'PASS',
    no_future_leakage: true, random_fallback_allowed: false, final_selection_randomness: false,
    purchase_lines_required: 3, numbers_per_line: 6, failed_gates: [], unevaluated_gates: [],
    prospective_confirmation_status: 'PASS'
  };
  const strict = { ...gate };
  const seal = {
    status: 'SEALED', target_round: 1252, data_cutoff: 1251, data_sha256: dataSha,
    candidate_model: 'SYNTHETIC_MODEL', allocator: 'SYNTHETIC_ALLOCATOR',
    purchase_lines: readyFile, line_count: 3, numbers_per_line: 6, geometry: 'DISJOINT_UNION18',
    prospective_confirmation_status: 'PASS', code_sha256: codeSha,
    purchase_lines_sha256: linesSha, seal_sha256: sealSha
  };
  const artifact = {
    exists: true, public: false, delivery_claim: false, path: readyFile,
    target_round: 1252, data_cutoff: 1251, data_sha256: dataSha,
    line_count: 3, numbers_per_line: 6, geometry: 'DISJOINT_UNION18',
    code_sha256: codeSha, file_sha256: linesSha, seal_sha256: sealSha
  };
  return { gate, strict, seal, artifact };
}

const cases = [];
function record(name, result, expected) {
  assert.equal(result.decision, expected, name);
  assert.equal(result.read_line_values, false, name + ' must never read or return line values');
  cases.push({ name, decision: result.decision, reasons: result.reasons.length });
}

// Actual target-1252 repository state: metadata only; the line artifact itself is never opened.
const actual = {
  gate: readJson('research/weekly_purchase/1252/MODEL_GATE_1252_20261127.json'),
  strict: readJson('research/weekly_purchase/1252/STRICT_PASS_STATUS_1252_20261127.json'),
  seal: readJson('research/weekly_purchase/1252/FREEZE_SEAL_STATUS_1252_20261123.json'),
  artifact: {
    exists: fs.existsSync(path.join(root, 'research/weekly_purchase/1252/RESEARCH_SELECTED_LINES_1252_20261127.json')),
    public: true, delivery_claim: true,
    path: 'research/weekly_purchase/1252/RESEARCH_SELECTED_LINES_1252_20261127.json',
    target_round: 1252, data_cutoff: 1251,
    data_sha256: '2017cf2b76454011bf11567a40a491311bedcdf6aaf47179beba5cb399c30cb9',
    line_count: 3, numbers_per_line: 6, geometry: 'DISJOINT_UNION18'
  }
};
const actualResult = evaluateDeliveryEligibility(actual);
record('actual_target_1252_state', actualResult, 'SUPPRESS');
assert.equal(actualResult.public_artifact_conflict, true);
assert.equal(actualResult.delivery_claim_present, true);

{
  const f = readyFixture(); f.gate.status = 'NOT_READY'; f.strict.status = 'NOT_READY';
  f.gate.strict_pass_ready = false; f.strict.strict_pass_ready = false;
  record('not_ready_state', evaluateDeliveryEligibility(f), 'SUPPRESS');
}
{
  const f = readyFixture(); f.seal = null;
  record('missing_seal', evaluateDeliveryEligibility(f), 'SUPPRESS');
}
{
  const f = readyFixture(); f.seal.data_cutoff = 1250;
  record('cutoff_mismatch', evaluateDeliveryEligibility(f), 'SUPPRESS');
}
{
  const f = readyFixture(); f.strict.data_sha256 = sha('e');
  record('data_hash_mismatch', evaluateDeliveryEligibility(f), 'SUPPRESS');
}
{
  const f = readyFixture(); f.gate.unevaluated_gates = ['any3'];
  record('unevaluated_gate', evaluateDeliveryEligibility(f), 'SUPPRESS');
}
{
  const f = readyFixture(); f.gate.prospective_confirmation_status = 'UNSPECIFIED';
  record('prospective_confirmation_missing', evaluateDeliveryEligibility(f), 'SUPPRESS');
}
{
  const f = readyFixture(); f.strict.random_fallback_allowed = true;
  record('random_fallback_enabled', evaluateDeliveryEligibility(f), 'SUPPRESS');
}
{
  const f = readyFixture(); f.artifact.file_sha256 = sha('f');
  record('artifact_file_hash_mismatch', evaluateDeliveryEligibility(f), 'SUPPRESS');
}
{
  const f = readyFixture();
  record('synthetic_complete_ready_fixture', evaluateDeliveryEligibility(f), 'ALLOW_READ_FROZEN_ARTIFACT');
}

process.stdout.write(JSON.stringify({
  study_id: 'E085_STRICT_GATED_VISIBILITY_GUARD_AUDIT_v1',
  test_count: cases.length,
  pass_count: cases.length,
  fail_count: 0,
  cases,
  actual_target_1252: {
    decision: actualResult.decision,
    public_artifact_conflict: actualResult.public_artifact_conflict,
    delivery_claim_present: actualResult.delivery_claim_present,
    line_values_read: false
  },
  note: 'Synthetic fixture validates only guard eligibility metadata; it is not a real model, seal, or purchase artifact.'
}, null, 2) + '\n');
