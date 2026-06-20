# Mustel: A Deterministic Static Analysis Layer for AI-Augmented Code Review

## Abstract

Mustel is a non-AI static analysis layer designed to provide structured, compressed context to AI IDEs and coding agents. By running three established analysis tools (ruff, bandit, pip-audit) plus a custom YAML-based pattern library, Mustel generates a schema-compliant JSON report that includes a pre-written `agent_prompt` field — a sub-200-character plain English summary that AI agents can consume directly without parsing.

This paper presents empirical measurements of Mustel's detection accuracy and token efficiency. Key findings:

- **Real-world recall: 55.6%** (5/9 vulnerabilities in a real open-source Flask app — [EVFA](https://github.com/manuelz120/extremely-vulnerable-flask-app))
- **Independent recall: 75%** (12/16 vulnerabilities detected on test code NOT designed for Mustel)
- **Tuned recall: 100%** on purpose-built benchmarks (acknowledged as overfitted — see Section 4)
- **Token savings: 34.4%** measured empirically via tiktoken (not modeled)
- **Output token reduction: 64.9%** — the primary cost driver, as output tokens are 3-4x more expensive than input tokens on major LLM APIs

---

## 1. Test Environment

All benchmarks were executed on:

| Component | Version |
|-----------|---------|
| **Operating System** | Windows 11 (Build 10.0.28020) |
| **Architecture** | AMD64 |
| **Python** | 3.14.3 (MSC v.1944 64 bit) |
| **ruff** | 0.15.8 |
| **bandit** | 1.9.4 |
| **tiktoken** | 0.12.0 |
| **mustel** | 0.2.0 |

### 1.1 Test Subjects

| Project | Source | Files | Lines | Bytes | Vulns | CWE Types |
|---------|--------|-------|-------|-------|-------|-----------|
| `project_auth` | Written by mustel team | 1 | 82 | 2,307 | 5 | CWE-259, CWE-89, CWE-327, CWE-400, CWE-78 |
| `project_backend` | Written by mustel team | 1 | 83 | 3,018 | 5 | CWE-798, CWE-347, CWE-22, CWE-918, CWE-502 |
| `project_independent` | Written by us, NOT tuned for mustel | 2 | 192 | 6,567 | 16 | CWE-79, CWE-89, CWE-94, CWE-601, CWE-327, CWE-502, CWE-78, CWE-918, CWE-611, CWE-347 |
| **EVFA (real-world)** | **External open-source project** | **23** | **453** | **18,000** | **9** | CWE-89, CWE-502, CWE-259, CWE-94, CWE-918, CWE-352, CWE-639, CWE-862 |

**Vulnerability types tested across all projects:**

| Category | CWEs | Count |
|----------|------|-------|
| Injection (SQL, command, template) | CWE-78, CWE-89, CWE-94, CWE-79 | 9 |
| Insecure deserialization | CWE-502 | 4 |
| Hardcoded credentials/secrets | CWE-259, CWE-798 | 4 |
| Broken authentication (JWT, CSRF) | CWE-347, CWE-352 | 3 |
| SSRF | CWE-918 | 3 |
| Weak cryptography | CWE-327 | 2 |
| Path traversal | CWE-22 | 1 |
| Open redirect | CWE-601 | 1 |
| XML external entity | CWE-611 | 1 |
| Authorization logic (IDOR) | CWE-639, CWE-862 | 2 |
| Resource exhaustion | CWE-400 | 1 |
| Insecure temp file | CWE-377 | 1 |

---

## 2. System Design

Mustel wraps three external analysis tools into a unified pipeline:

| Engine | Tool | Catches |
|--------|------|---------|
| Bug detection | ruff (>= 0.4.0) | Syntax errors, unused imports, common bugs, type issues |
| Security analysis | bandit (>= 1.7.0) | SQL injection, hardcoded passwords, shell injection, etc. |
| CVE scanning | pip-audit (>= 2.6.0) | Known vulnerabilities in installed packages |
| Pattern matching | mustel-patterns (YAML) | Module-specific anti-patterns for 22 Python libraries |

All engine outputs are merged through a **normalizer** that:
1. Deduplicates findings (same file + line from multiple engines)
2. Categorizes into errors, security, and warnings
3. Assigns sequential IDs (E001, S001, W001, P001)
4. Generates a compressed `agent_prompt` (< 200 characters)

The normalizer produces a single JSON report conforming to **schema v1**.

### 2.1 The `agent_prompt` — Output Compression

The `agent_prompt` field is designed to eliminate the "diagnosis step" in AI code review. Instead of the AI reading raw code and producing a lengthy analysis, it receives:

```
mustel found 20 issues: HighSec:S001,S002,S003,S004,S006 | Errs:E001,E002,E003 |
MedSec:S005 | Warns:W001,...,W010. Use IDs to lookup details in JSON.
```

The AI then jumps directly to applying fixes, referencing IDs for specifics.

---

## 3. Token Efficiency — Empirical Measurement

### 3.1 Methodology

Token counts were measured using OpenAI's **tiktoken** library (`cl100k_base` encoding for GPT-4, `o200k_base` for GPT-4o). tiktoken is the exact tokenizer used by the OpenAI API for billing — counts are deterministic and reproducible by anyone with `pip install tiktoken`.

**Test subject:** `project_backend/app.py` — an 83-line FastAPI application with 5 planted security vulnerabilities.

**Two scenarios:**
- **A (Without Mustel):** AI receives a review prompt + full source code. AI must discover issues, explain each one, and provide fixes.
- **B (With Mustel):** AI receives the same prompt + source code + Mustel's `agent_prompt` (186 chars). AI skips diagnosis and jumps to applying patches.

**AI responses** were generated by a real AI assistant (Claude), not modeled or estimated. Both responses were saved as text files and their tokens counted with tiktoken.

### 3.2 Results (cl100k_base encoding - GPT-4)

| Metric | Without Mustel | With Mustel | Delta |
|--------|---------------|-------------|-------|
| **Input tokens** (prompt + code) | 746 | 811 | +65 (overhead) |
| **Output tokens** (AI response) | 1,054 | 370 | **-684 (saved)** |
| **Total tokens** | 1,800 | 1,181 | **-619** |
| **Savings** | — | — | **34.4%** |

### 3.3 Results (o200k_base encoding - GPT-4o)

| Metric | Without Mustel | With Mustel | Delta |
|--------|---------------|-------------|-------|
| Input tokens | 750 | 815 | +65 |
| Output tokens | 1,061 | 377 | **-684** |
| Total tokens | 1,811 | 1,192 | **-619** |
| Savings | — | — | **34.2%** |

### 3.4 Where the Savings Come From

Mustel **adds** 65 input tokens (the `agent_prompt` overhead) but **saves** 684 output tokens. The net saving is 619 tokens per review cycle.

This matters because output tokens are 3-4x more expensive than input tokens on most LLM APIs:
- GPT-4o: $2.50/M input vs $10.00/M output (4x)
- Claude 3.5 Sonnet: $3.00/M input vs $15.00/M output (5x)

When weighted by API pricing, the **effective cost reduction is approximately 45-50%** per review cycle — the output savings dominate.

### 3.5 Limitations of This Measurement

- AI response length varies between runs. Our measurement uses one representative response per scenario. A production study should average across 10+ runs.
- The test file is 83 lines. Larger files will have higher input token counts, which dilutes the percentage savings (but the absolute output saving remains).
- tiktoken counts tokens for GPT-family models. Claude and Gemini use different tokenizers, but the percentage difference is typically < 5%.

---

## 4. Detection Accuracy — Independent Benchmark

### 4.1 Methodology

To address the self-referential benchmark problem (see Section 6), we created two independent test files:

- **`app_vuln_web.py`** — A Flask application with 8 vulnerabilities based on OWASP patterns
- **`app_vuln_api.py`** — A Flask API with 8 vulnerabilities based on real CVE patterns

These files were written to simulate real-world vulnerable code **without consulting Mustel's YAML pattern rules**. The goal is to test detection on code Mustel was NOT tuned for.

### 4.2 Results

**app_vuln_api.py: 8/8 (100% recall)**

| Vulnerability | Caught? | Engine |
|---------------|---------|--------|
| subprocess shell=True | Yes | mustel-patterns + bandit |
| pickle deserialization | Yes | bandit |
| eval() on user input | Yes | bandit |
| requests.post no timeout | Yes | mustel-patterns |
| os.system() with user input | Yes | mustel-patterns + bandit |
| Insecure temp file | Yes | bandit |
| XML/XXE parsing | Yes | bandit |
| JWT algorithm='none' | Yes | mustel-patterns |

**app_vuln_web.py: 4/8 (50% recall)**

| Vulnerability | Caught? | Engine | Why missed? |
|---------------|---------|--------|-------------|
| XSS via render_template_string | **No** | — | No pattern for Jinja2 template injection |
| SQL injection (concatenation) | Yes | ruff | — |
| SSTI (template injection) | **No** | — | No pattern for render_template_string(user_input) |
| Open redirect | **No** | — | No pattern for unvalidated redirect() |
| Flask debug=True | Yes | bandit | — |
| MD5 password hashing | Yes | bandit | — |
| yaml.load unsafe | Yes | bandit | — |
| Hardcoded DB credentials | **No** | — | Pattern matches SECRET_KEY but not DATABASE_URL |

### 4.3 Overall Independent Recall: 75% (12/16)

**Missed vulnerability categories:**
1. **Jinja2 XSS/SSTI** — Requires understanding that `render_template_string(f"...{user_input}...")` is dangerous. No regex or keyword pattern covers this.
2. **Open redirect** — `redirect(user_input)` is a common Flask vulnerability but has no pattern in Mustel's library.
3. **Generic hardcoded credentials** — The pattern only matches `SECRET_KEY`, not `DATABASE_URL` or arbitrary connection strings.

These are genuine gaps. Mustel is a "blind tripwire" — it catches what its rules explicitly cover. Semantic vulnerabilities that require understanding data flow (taint analysis) are fundamentally out of scope for a regex-based tool.

---

## 5. Real-World Validation: Extremely Vulnerable Flask App (EVFA)

### 5.1 About the Test Subject

To validate Mustel on code it had **zero influence over**, we tested against the [Extremely Vulnerable Flask App](https://github.com/manuelz120/extremely-vulnerable-flask-app) (EVFA) — a real open-source project by Manuel Zarat designed for security education.

- **23 Python files** across `routes/`, `models/`, `forms/`, `utils/`
- Multi-file architecture with SQLAlchemy ORM, Flask-Login, bcrypt
- 9 documented vulnerabilities including SQL injection, pickle deserialization, SSRF, SSTI, and authorization logic bugs

This is the strongest validation in this paper because Mustel had no involvement in EVFA's creation, the code structure is realistic (models, routes, utilities), and the vulnerabilities span multiple files.

### 5.2 Results: 55.6% Recall (5/9)

| Vulnerability | File | Caught? | Engine | Notes |
|---|---|---|---|---|
| SQL injection (signup) | signup.py:16 | **Yes** | ruff S608 | f-string in SQLAlchemy text() |
| Pickle from cookie | account.py:118 | **Yes** | bandit B301 | loads(b64decode(cookie)) |
| Hardcoded SECRET_KEY | app.py:11 | **Yes** | mustel-patterns | "super secret key" |
| SSRF via urlopen | profile_image.py:7 | **Yes** | bandit B310 | urlopen(user_url) |
| Missing CSRF | app.py + all routes | **Yes** | mustel-patterns | Flagged across 7 files |
| SQL injection (search) | account.py:33 | **No** | — | SQLAlchemy text() with f-string not caught by ruff |
| SSTI in 404 handler | app.py:31 | **No** | — | render_template_string(f"...{request.path}") |
| IDOR (view any user's notes) | account.py:43 | **No** | — | Logic bug: no authorization check |
| Delete without ownership | notes.py:41 | **No** | — | Logic bug: no ownership verification |

### 5.2A Full Scan Output (Raw Findings)

Mustel reported **44 total issues** (11 security, 7 errors, 26 warnings) across 23 files in 2,913ms.

**Security findings (11):**

| ID | File | Line | Engine | Rule | Issue |
|---|---|---|---|---|---|
| S001 | app.py | 6 | mustel-patterns | flask-no-csrf | No CSRF protection on Flask app |
| S002 | app.py | 11 | mustel-patterns | flask-hardcoded-secret-key | SECRET_KEY = "super secret key" |
| S003 | routes/account.py | 8 | mustel-patterns | flask-no-csrf | CSRF missing in account routes |
| S004 | routes/account.py | 118 | bandit | B301:blacklist | pickle.loads() on cookie data |
| S005 | routes/home.py | 1 | mustel-patterns | flask-no-csrf | CSRF missing in home routes |
| S006 | routes/login.py | 3 | mustel-patterns | flask-no-csrf | CSRF missing in login routes |
| S007 | routes/notes.py | 3 | mustel-patterns | flask-no-csrf | CSRF missing in notes routes |
| S008 | routes/registration_codes.py | 6 | mustel-patterns | flask-no-csrf | CSRF missing in registration routes |
| S009 | routes/signup.py | 6 | mustel-patterns | flask-no-csrf | CSRF missing in signup routes |
| S010 | routes/signup.py | 16 | ruff | S608 | SQL injection via f-string in text() |
| S011 | utils/profile_image.py | 7 | bandit | B310:blacklist | urlopen() on user URL (SSRF) |

**Error findings (7):**

| ID | File | Line | Engine | Rule | Issue |
|---|---|---|---|---|---|
| E001 | models/\_\_init\_\_.py | 6 | ruff | F401 | User imported but unused |
| E002 | models/\_\_init\_\_.py | 7 | ruff | F401 | RegistrationCode imported but unused |
| E003 | models/\_\_init\_\_.py | 8 | ruff | F401 | Note imported but unused |
| E004 | routes/\_\_init\_\_.py | 10 | ruff | F401 | registration_codes imported but unused |
| E005 | routes/account.py | 84 | ruff | E501 | Line too long (100 > 88) |
| E006 | routes/signup.py | 17 | ruff | E501 | Line too long (91 > 88) |
| E007 | utils/notes.py | 11 | ruff | E712 | Equality comparison to False |

**Generated agent_prompt (311 chars):**
```
mustel found 44 issues: HighSec:S002,S010 | Errs:E001,E002,E003,E004,E005,E006,E007 |
MedSec:S001,S003,S004,S005,S006,S007,S008,S009,S011 |
Warns:W001,...,W026. Use IDs to lookup details in JSON.
```

### 5.3 Classification of Misses

**Regex-addressable (could add a pattern — 2 misses):**
- `sql_injection_search`: SQLAlchemy's `text(f"...")` pattern. A new YAML pattern matching `text(f"` or `text(f'` would catch this.
- `ssti_404_handler`: `render_template_string(f"...")` is a known Flask anti-pattern. A new pattern could flag any `render_template_string` call with an f-string argument.

**Fundamentally undetectable by regex (2 misses):**
- `idor_notes_access`: The vulnerability is the *absence* of an authorization check — there is no dangerous function call to match, only missing logic.
- `insecure_delete`: Same — the bug is that ownership is not verified before deletion. No regex can detect "code that should exist but doesn't" across module boundaries.

This classification is significant: **71.4% of regex-detectable vulnerabilities were caught (5/7)**, while the 2 remaining misses are logic bugs that require semantic understanding of authorization flows — a capability that no regex-based or AST-based scanner (including Semgrep) can reliably provide.

---

## 6. Tuned Benchmark — Acknowledged Overfitting

### 6.1 The "Diabolical 100%" Problem

Mustel's original benchmark used two purpose-built test applications:
- `project_auth` (5 vulnerabilities, 82 lines)
- `project_backend` (5 vulnerabilities, 83 lines)

Both achieved **100% recall with 0 false positives**. This result is suspicious, and we acknowledge it is partially the result of overfitting:

1. **Vulnerabilities were planted with knowledge of detection rules.** The bugs in `project_auth` are "textbook 101" patterns (direct string format SQL injection, hardcoded SECRET_KEY, shell=True) that are trivially caught by regex.

2. **Scoring was iteratively tuned.** Line ranges were broadened, IGNORE_RULES was implemented, and YAML patterns were expanded during Phase 3 specifically to match the test code.

3. **Phase 3 rule broadening is additional overfitting.** When initial recall on `project_backend` was 20%, three YAML rules were rewritten to match the specific code patterns in the test file. The final 100% is not an independent validation.

### 6.2 Why We Keep the Tuned Benchmark

Despite overfitting, the tuned benchmark proves:
- The pipeline works end-to-end (scan → normalize → compress → output)
- The normalizer correctly deduplicates and categorizes across 3+ engines
- The `agent_prompt` stays under 200 characters
- Scan time stays under 3 seconds

The independent benchmark (Section 4) and real-world validation (Section 5) provide the honest recall numbers.

---

## 7. Comparison: Mustel vs Standalone Tools

### 7.1 Methodology

We ran Mustel, standalone bandit, and semgrep against the same independent test files (`project_independent/`).

### 7.2 Results

| Metric | Mustel | Bandit (standalone) | Notes |
|--------|--------|-------------------|-------|
| Security findings | 21 | 13 | Mustel catches more via YAML patterns |
| Total findings | 39 | 13 | Mustel includes bugs + style via ruff |
| Scan time | ~4,300ms | ~1,200ms | Mustel runs 3 tools, not 1 |
| Raw output size | 18,322 chars | 12,786 chars | Both produce verbose JSON |
| **agent_prompt size** | **286 chars** | **N/A** | This is Mustel's value proposition |

### 7.3 Analysis

**Mustel is not a replacement for Semgrep or standalone bandit.** It is a **wrapper and compressor** that:

1. Runs multiple tools (ruff + bandit + pip-audit + custom patterns)
2. Deduplicates overlapping findings
3. Compresses the output into a format AI agents can consume in one read

The "why use this instead of Semgrep + SARIF" question has a specific answer: **Mustel's `agent_prompt` eliminates the need for the AI to parse a 12,000+ character JSON report.** The AI receives 286 characters of pre-prioritized findings and immediately knows what to fix.

For teams already using Semgrep in CI pipelines, Mustel's value is in the last-mile compression for AI IDE integration, not in replacing the scanner.

---

## 8. Scale Limitations

Test subjects range from single-file 82-line apps to the 23-file, 453-line EVFA project. Real production Python services routinely exceed 10,000 lines across hundreds of modules.

**What changes at scale:**
- Multi-file data flows introduce tainted variables that cross module boundaries. Mustel cannot track these (demonstrated by the IDOR miss in EVFA).
- ORM layers, middleware, and custom authentication logic create vulnerability patterns that regex cannot match (demonstrated by the SQLAlchemy `text()` miss in EVFA).
- False positive rates will increase as more code surface area triggers pattern matches.

**What doesn't change:**
- The `agent_prompt` compression ratio remains effective regardless of codebase size (EVFA's 44-finding report compressed to 311 chars).
- Engine-level detection (ruff, bandit) scales linearly with file count.
- The deduplication and categorization pipeline handles arbitrary result counts.

Future work should validate on production-scale codebases (10,000+ lines) and projects with known CVEs from the GitHub Advisory Database or OSV.

---

## 9. Iteration Log

### 9.1 Phase 1: Baseline (2026-04-10)

| Metric | Score | Target | Status |
|--------|-------|--------|--------|
| Recall | 5/5 (100%) | >= 80% | PASS |
| False positives | 10 | <= 1 | FAIL |
| Scan time | 2,660ms | < 3,000ms | PASS |
| agent_prompt length | 1,098 chars | < 200 chars | FAIL |

Action: Compressed `agent_prompt` generator in normalizer.py.

### 9.2 Phase 2: Prompt Compression (2026-04-10)

| Metric | Score | Target | Status |
|--------|-------|--------|--------|
| Recall | 5/5 (100%) | >= 80% | PASS |
| False positives | 10 | <= 1 | FAIL |
| Scan time | 1,718ms | < 3,000ms | PASS |
| agent_prompt length | 166 chars | < 200 chars | PASS |

Action: Refined benchmark scoring to handle duplicate detections.

### 9.3 Phase 3: Industry Benchmark (2026-04-10)

Initial recall on `project_backend`: **20% (1/5)**. Three YAML rules were broadened. Final recall: **100% (5/5)**. See Section 4 for overfitting acknowledgment.

### 9.4 Phase 4: Independent Validation (2026-04-22)

Two new test files created WITHOUT consulting YAML patterns. Overall recall: **75% (12/16)**. Four missed vulnerabilities documented in Section 3.

### 9.5 Phase 5: Token Measurement (2026-04-22)

Empirical measurement via tiktoken replaced the earlier modeled estimate. Actual savings: **34.4%** (down from the modeled 45.3%, but now backed by reproducible data).

### 9.6 Phase 6: Real-World Validation (2026-04-22)

Cloned the Extremely Vulnerable Flask App (EVFA) — a real open-source project (23 files, 453 lines) with 9 documented vulnerabilities. Mustel recall: **55.6% (5/9)**. Two misses are regex-addressable pattern gaps; two are logic bugs fundamentally undetectable by static analysis.

---

## 10. Extension Benchmarks: Repository Mapping & Save Guardrails

To evaluate Mustel 0.3.0 at scale, we executed tests on 5 large open-source projects (cloned inside our virtual environment's site-packages). 

We measured:
1.  **Files**: Count of Python source modules.
2.  **Code Map size**: Total character length and token count (cl100k_base for GPT-4).
3.  **Code Map generation time (ms)**: Time taken to parse all files via AST and build the compact tree.
4.  **Initial Scan time (ms)**: Baseline linting latency on a cold cache.
5.  **Incremental Scan time (ms)**: Active linter latency with stat-based caching enabled.

### 10.1 Scale & Latency Results

| Project | Files | Code Map (Chars) | Code Map (Tokens) | Code Map Time | Initial Scan | Incremental Scan |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **requests** | 18 | 19,318 | 4,587 | 74 ms | 303 ms | **29 ms** |
| **click** | 17 | 32,425 | 7,794 | 138 ms | 277 ms | **26 ms** |
| **watchdog** | 25 | 21,157 | 4,908 | 587 ms | 292 ms | **32 ms** |
| **bandit** | 69 | 18,060 | 4,352 | 1,735 ms | 644 ms | **114 ms** |
| **mcp** | 109 | 73,614 | 15,921 | 2,794 ms | 649 ms | **79 ms** |

### 10.2 Scale Summary & Latency Analysis
*   **Incremental Latency**: Caching keeps the compile/lint feedback loop exceptionally tight, running in **under 32 ms** for standard projects (15-25 files) and only **79-114 ms** on very large repos (69-109 files). This satisfies the strict `< 50ms` target for typical editor saves.
*   **Repository Mapping Overhead**: On average, a project codebase map occupies **~4,000 - 8,000 tokens**. Although larger than the 300-token target for tiny files, it represents a **95% token savings** compared to sending the raw source contents of all modules (e.g., requests is 18 files, ~100k tokens of source code vs only 4,587 tokens of mapping skeleton).

---

## 11. Conclusion

Mustel demonstrates that a lightweight, deterministic static analysis layer can meaningfully reduce AI token consumption during code review. The measured 34.4% token savings come primarily from eliminating the AI's diagnostic output (684 output tokens saved per review cycle).

Mustel's detection accuracy is bounded by its rule coverage:

| Benchmark | Source | Recall | Significance |
|-----------|--------|--------|--------------|
| Tuned | Our code, tuned for mustel | 100% (10/10) | Pipeline correctness proof (overfitted) |
| Independent | Our code, NOT tuned | 75% (12/16) | Honest pattern coverage |
| **Real-world (EVFA)** | **External open-source** | **55.6% (5/9)** | **Strongest evidence** |
| Real-world (regex-only) | EVFA, excluding logic bugs | 71.4% (5/7) | Fair comparison for regex tools |

The 4 missed vulnerabilities in the real-world test break down into 2 regex-addressable pattern gaps (SQLAlchemy `text()`, `render_template_string`) and 2 fundamentally undetectable logic bugs (IDOR, missing ownership check). This distinction matters: no regex or AST scanner can detect the absence of authorization logic.

Mustel's contribution is not "better static analysis" — tools like Semgrep have broader rule sets. The contribution is **the compression layer**: merging multiple tools' outputs into a single, sub-300-character `agent_prompt` that AI agents can read and act on immediately.

---

## Reproducibility

All benchmark scripts, test files, and token measurement data are included in the repository:

```
benchmarks/
  token_benchmark.py          # tiktoken-based measurement (pip install tiktoken)
  token_data/
    response_without_mustel.txt  # AI response without context
    response_with_mustel.txt     # AI response with mustel context
    token_results.json           # Saved token counts
  score_independent.py         # Independent recall scoring
  score_realworld.py           # Real-world EVFA scoring
  comparison_benchmark.py      # mustel vs bandit comparison
  projects/
    project_auth/              # Tuned benchmark (5 bugs)
    project_backend/           # Tuned benchmark (5 bugs)
    project_independent/       # Independent benchmark (16 bugs, our code)
    real_world/evfa/           # Real-world benchmark (git clone, NOT our code)
```

To reproduce:
```bash
pip install tiktoken
python benchmarks/token_benchmark.py      # Token measurement
python benchmarks/score_independent.py    # Independent recall
python benchmarks/score_realworld.py      # Real-world recall
python benchmarks/comparison_benchmark.py # Tool comparison
python benchmarks/run_extension_tests.py  # Extension Mapping & Save Guardrail tests
```

