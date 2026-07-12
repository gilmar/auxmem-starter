"""Version identifiers for Koinome releases.

Three coordinated versions are tracked:

* **CLI** (`__version__` in ``koinome/__init__.py``, ``pyproject.toml``): the
  Koinome package on PyPI.
* **Template** (``TEMPLATE_VERSION``, manifest ``template_version``): corpus
  folder tooling and guidance adopted via ``koinome upgrade``.
* **Conformance** (``CONFORMANCE_VERSION``, manifest ``conformance_version``):
  the validator and ``check_corpus`` contract. Bump when rules change what
  constitutes a valid note — a compatibility-relevant change.

Versioning is paused at ``0.0.0`` until the hardening cycle completes and an
intentional prerelease is published. See ``docs/RELEASE.md``.
"""
TEMPLATE_VERSION = "0.0.0"
CONFORMANCE_VERSION = "0.0.0"
