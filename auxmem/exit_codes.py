"""CLI exit codes for the auxmem command.

0  OK                 operation succeeded; auxmem is conformant when checked
1  OPERATION_FAILED   usage error, subprocess failure, or unexpected operation error
2  NON_CONFORMANT     operation ran but the resulting auxmem failed validation
3  CONFLICT           conflict or quarantine branch created (reserved for sync)
"""

OK = 0
OPERATION_FAILED = 1
NON_CONFORMANT = 2
CONFLICT = 3
