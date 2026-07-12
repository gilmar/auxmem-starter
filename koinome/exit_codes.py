"""CLI exit codes for the corpus command.

0  OK                 operation succeeded; corpus is conformant when checked
1  OPERATION_FAILED   usage error, subprocess failure, or unexpected operation error
2  NON_CONFORMANT     operation ran but the resulting corpus failed validation
3  CONFLICT           conflict or quarantine branch created (reserved for sync)
"""

OK = 0
OPERATION_FAILED = 1
NON_CONFORMANT = 2
CONFLICT = 3
