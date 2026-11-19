from __future__ import annotations

import unittest
from pathlib import Path


class E073QueuePersistenceContractTests(unittest.TestCase):
    def test_completed_execution_status_is_persisted_before_audit(self):
        workflow = Path(
            ".github/workflows/target-1251-e073-three-draw-membership-count.yml"
        ).read_text(encoding="utf-8")
        status_update = workflow.index('task["execution_status"] =')
        queue_persist = workflow.index(
            'queue_path.write_text(json.dumps(queue, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")'
        )
        audit_read = workflow.index(
            'audit = json.loads(Path("research/weekly_purchase/1251/THREE_LINE_READINESS_AUDIT_20261115.json")'
        )
        self.assertLess(status_update, queue_persist)
        self.assertLess(queue_persist, audit_read)


if __name__ == "__main__":
    unittest.main()
