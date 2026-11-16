# Git Workflow & Version Control Guidelines

## J.A.R.V.I.S. Engineering Practices & Repository Standard

---

## 1. Branching Strategy (Git Flow / Trunk-Based Development)

The repository follows a structured branch workflow designed for continuous integration, safety, and traceability:

* **`main` (Production Branch)**:
  * Protected branch representing deployable, tested, production-grade releases.
  * Direct commits to `main` are restricted in production teams.
* **`develop` (Integration Branch)**:
  * Central integration branch for ongoing sprint cycles.
* **`feature/*` (Feature Branches)**:
  * Created from `develop` or `main` for individual features or capabilities.
  * Example naming: `feature/websocket-telemetry`, `feature/react-dashboard`, `feature/redis-cache`.
* **`bugfix/*` / `hotfix/*` (Patch Branches)**:
  * Short-lived branches dedicated to immediate issue resolution.
  * Example naming: `fix/disk-partition-scan`, `fix/jwt-expiration`.
* **`release/*` (Release Branches)**:
  * Stabilization branches for release tagging and pre-flight validation.

---

## 2. Conventional Commits Specification

All commits must adhere to the Conventional Commits specification to support automated changelogs and semantic release tagging:

```
<type>(<scope>): <short imperative description>

[optional body providing technical context]

[optional footer referencing issue/PR numbers]
```

### Commit Types:
* **`feat`**: A new user-facing feature or API capability (e.g., `feat(auth): implement JWT issuance and PBKDF2 password hashing`).
* **`fix`**: A bug fix or error mitigation (e.g., `fix(system): skip unready optical drives in psutil disk scan`).
* **`docs`**: Documentation updates or architectural specifications (e.g., `docs: update PRD, HLD, and LLD with 50 concepts`).
* **`test`**: Adding missing tests or refactoring test suites (e.g., `test(api): add automated integration tests for payments and SSR`).
* **`refactor`**: Code restructuring without altering external functionality.
* **`chore`**: Maintenance, build configs, or dependency updates.

---

## 3. Pull Request (PR) & Code Review Workflow

1. **Local Pre-Flight Checks**:
   * Before pushing a branch, all unit and integration tests must pass:
     ```bash
     pytest tests/ -v
     ```
   * Frontend static bundle must build without warnings:
     ```bash
     cd web && npm run build
     ```
2. **Opening a Pull Request**:
   * Target branch: `main` or `develop`.
   * PR Title: Must follow Conventional Commits format.
   * PR Description: Includes context, architectural impact, and verification steps.
3. **Peer Review & Automated CI Gates**:
   * Requires at least one approving peer review.
   * Continuous Integration tests must return exit code 0.
4. **Merge Strategy**:
   * **Squash and Merge**: Used for small multi-commit feature branches to maintain a clean linear commit history on `main`.
   * **Rebase and Merge**: Used for major releases preserving distinct architectural milestones.

---

## 4. Semantic Versioning & Release Tagging

Releases follow Semantic Versioning (`MAJOR.MINOR.PATCH`):
* `MAJOR`: Incompatible breaking architectural changes.
* `MINOR`: Backward-compatible new capabilities (e.g., v2.0.0 adding RESTful microservices and React Web HUD).
* `PATCH`: Backward-compatible bug fixes and optimizations.

Creating an annotated release tag:
```bash
git tag -a v2.0.0 -m "Release v2.0.0: Fullstack Edge Ecosystem with Multi-Step Agent, REST, WebSockets & React HUD"
git push origin v2.0.0
```
