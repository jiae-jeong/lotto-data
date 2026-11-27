'use strict';

/*
 * E085 strict-gated visibility guard.
 * Metadata-only by design: this module never reads or returns lottery line values.
 */
function evaluateDeliveryEligibility(input) {
  const x = input || {};
  const gate = x.gate || null;
  const strict = x.strict || null;
  const seal = x.seal || null;
  const artifact = x.artifact || null;
  const reasons = [];
  const add = (code, ok) => { if (!ok) reasons.push(code); };
  const empty = value => value == null || value === '';
  const isSha256 = value => typeof value === 'string' && /^[a-f0-9]{64}$/i.test(value);
  const emptyArray = value => !Array.isArray(value) || value.length === 0;

  add('GATE_RECORD_MISSING', !!gate);
  add('STRICT_STATUS_RECORD_MISSING', !!strict);
  add('SEAL_RECORD_MISSING', !!seal);

  if (gate && strict) {
    add('TARGET_ROUND_MISMATCH', gate.target_round === strict.target_round);
    add('CUTOFF_MISMATCH', gate.data_cutoff === strict.data_cutoff);
    add('DATA_SHA_MISMATCH', gate.data_sha256 === strict.data_sha256);
    add('GATE_STATUS_NOT_STRICT_PASS_READY', gate.status === 'STRICT_PASS_READY');
    add('STRICT_STATUS_NOT_STRICT_PASS_READY', strict.status === 'STRICT_PASS_READY');
    add('GATE_STRICT_PASS_FALSE', gate.strict_pass_ready === true);
    add('STRICT_PASS_FALSE', strict.strict_pass_ready === true);
    add('GATE_MODEL_VALIDATION_FAIL', gate.strict_model_validation_pass === true);
    add('STRICT_MODEL_VALIDATION_FAIL', strict.strict_model_validation_pass === true);
    add('GATE_PORTFOLIO_FAIL', gate.strict_portfolio_pass === true);
    add('STRICT_PORTFOLIO_FAIL', strict.strict_portfolio_pass === true);
    add('READY_FILE_NOT_PRESENT', gate.ready_file_exists === true && strict.ready_file_exists === true);
    add('READY_FILE_PATH_MISSING_OR_MISMATCHED',
      typeof gate.ready_file === 'string' && gate.ready_file.length > 0 && gate.ready_file === strict.ready_file);
    add('FREEZE_PERMISSION_FALSE',
      gate.final_purchase_freeze_allowed === true && strict.final_purchase_freeze_allowed === true);
    add('GATE_VERSION_MISSING',
      typeof gate.strict_gate_version === 'string' && gate.strict_gate_version.length > 0 &&
      gate.strict_gate_version === strict.strict_gate_version);
    add('GATE_EVALUATION_NOT_PASS', gate.strict_gate_evaluation === 'PASS');
    add('FUTURE_LEAKAGE_NOT_CLEARED', gate.no_future_leakage === true && strict.no_future_leakage === true);
    add('RANDOM_FALLBACK_ENABLED',
      gate.random_fallback_allowed === false && strict.random_fallback_allowed === false);
    add('FINAL_SELECTION_RANDOM',
      gate.final_selection_randomness === false && strict.final_selection_randomness === false);
    add('WRONG_PURCHASE_LINE_COUNT',
      gate.purchase_lines_required === 3 && strict.purchase_lines_required === 3);
    add('WRONG_NUMBERS_PER_LINE',
      gate.numbers_per_line === 6 && strict.numbers_per_line === 6);
    add('FAILED_GATE_REMAINS', emptyArray(gate.failed_gates) && emptyArray(strict.failed_gates));
    add('UNEVALUATED_GATE_REMAINS', emptyArray(gate.unevaluated_gates) && emptyArray(strict.unevaluated_gates));
    add('PROSPECTIVE_CONFIRMATION_NOT_PASSED',
      gate.prospective_confirmation_status === 'PASS' &&
      strict.prospective_confirmation_status === 'PASS');
  }

  if (seal && gate && strict) {
    add('SEAL_STATUS_NOT_SEALED', seal.status === 'SEALED');
    add('SEAL_TARGET_MISMATCH', seal.target_round === gate.target_round && seal.target_round === strict.target_round);
    add('SEAL_CUTOFF_MISMATCH', seal.data_cutoff === gate.data_cutoff && seal.data_cutoff === strict.data_cutoff);
    add('SEAL_DATA_SHA_MISMATCH', seal.data_sha256 === gate.data_sha256 && seal.data_sha256 === strict.data_sha256);
    add('SEAL_MODEL_MISSING', !empty(seal.candidate_model));
    add('SEAL_ALLOCATOR_MISSING', !empty(seal.allocator));
    add('SEAL_PURCHASE_FILE_MISSING',
      typeof seal.purchase_lines === 'string' && seal.purchase_lines.length > 0);
    add('SEAL_GEOMETRY_INVALID',
      seal.line_count === 3 && seal.numbers_per_line === 6 && seal.geometry === 'DISJOINT_UNION18');
    add('SEAL_PROSPECTIVE_CONFIRMATION_NOT_PASSED', seal.prospective_confirmation_status === 'PASS');
    add('SEAL_HASHES_MISSING',
      isSha256(seal.code_sha256) && isSha256(seal.data_sha256) &&
      isSha256(seal.purchase_lines_sha256) && isSha256(seal.seal_sha256));
  }

  if (artifact && gate && strict && seal) {
    add('READY_ARTIFACT_MISSING', artifact.exists === true);
    add('ARTIFACT_PATH_MISMATCH', artifact.path === gate.ready_file && artifact.path === seal.purchase_lines);
    add('ARTIFACT_TARGET_MISMATCH', artifact.target_round === gate.target_round);
    add('ARTIFACT_CUTOFF_MISMATCH', artifact.data_cutoff === gate.data_cutoff);
    add('ARTIFACT_DATA_SHA_MISMATCH', artifact.data_sha256 === gate.data_sha256);
    add('ARTIFACT_GEOMETRY_INVALID',
      artifact.line_count === 3 && artifact.numbers_per_line === 6 && artifact.geometry === 'DISJOINT_UNION18');
    add('ARTIFACT_CODE_SHA_MISMATCH', artifact.code_sha256 === seal.code_sha256);
    add('ARTIFACT_FILE_SHA_MISMATCH', artifact.file_sha256 === seal.purchase_lines_sha256);
    add('ARTIFACT_SEAL_SHA_MISMATCH', artifact.seal_sha256 === seal.seal_sha256);
  }

  const blocked = reasons.length > 0;
  return {
    decision: blocked ? 'SUPPRESS' : 'ALLOW_READ_FROZEN_ARTIFACT',
    reasons,
    artifact_present: artifact ? artifact.exists === true : false,
    public_artifact_conflict: !!(artifact && artifact.exists === true && artifact.public === true && blocked),
    delivery_claim_present: !!(artifact && artifact.delivery_claim === true),
    read_line_values: false
  };
}

module.exports = { evaluateDeliveryEligibility };
