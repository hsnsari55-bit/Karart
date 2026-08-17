import contextlib
import io
import unittest
from unittest import mock

from backend import run_real_field_validation


class TestRunRealFieldValidation(unittest.TestCase):
    def test_main_returns_nonzero_and_does_not_claim_success_on_pipeline_failure(self):
        failure = {
            "status": "FAILURE",
            "error_step": "constraint_solver",
            "error_msg": "Topology validation failed: Graph contains zero nodes.",
        }

        with mock.patch.object(
            run_real_field_validation,
            "RegressionTester",
        ) as tester_class, io.StringIO() as stdout, contextlib.redirect_stdout(stdout):
            tester_class.return_value.run_on_file.return_value = failure
            exit_code = run_real_field_validation.main()
            output = stdout.getvalue()

        self.assertEqual(exit_code, 1)
        self.assertNotIn("REAL FIELD DXF VALIDATION SUCCESSFUL", output)
        self.assertIn('"status": "FAILURE"', output)
        self.assertIn('"error_step": "constraint_solver"', output)

    def test_main_returns_zero_and_claims_success_only_on_pipeline_success(self):
        success = {"status": "SUCCESS"}

        with mock.patch.object(
            run_real_field_validation,
            "RegressionTester",
        ) as tester_class, io.StringIO() as stdout, contextlib.redirect_stdout(stdout):
            tester_class.return_value.run_on_file.return_value = success
            exit_code = run_real_field_validation.main()
            output = stdout.getvalue()

        self.assertEqual(exit_code, 0)
        self.assertIn('"status": "SUCCESS"', output)
        self.assertIn("REAL FIELD DXF VALIDATION SUCCESSFUL", output)


if __name__ == "__main__":
    unittest.main()