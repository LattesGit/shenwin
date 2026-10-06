# 🐰 SHENWIN

### OSINT Username Enumeration & Correlation Tool

SHENWIN is a lightweight Python-based OSINT tool for discovering usernames across a large collection of public platforms.

It combines multi-platform username enumeration, username variation generation, response analysis, confidence scoring, rate-limit awareness, fingerprinting, and structured result export into a single command-line workflow.

> Built for authorized OSINT, reconnaissance, security research, and username discovery.

---

## ✦ Features

### 🔎 Username Enumeration

- Large multi-category platform database
- Social media platforms
- Developer platforms
- Cybersecurity / CTF platforms
- Gaming platforms
- Music and streaming services
- Art and photography platforms
- Blogging and publishing platforms
- Forums and communities
- Education and coding platforms
- Professional platforms
- Link-in-bio services
- Support and monetization platforms
- Sports and fitness platforms
- Travel platforms
- Marketplaces
- Books, anime and media platforms
- Crypto / Web3 platforms
- Wiki and knowledge platforms

### 🧠 Detection Engine

SHENWIN does more than simply treat every `200 OK` response as a match.

The detection engine analyzes:

- HTTP status codes
- Response body content
- Page titles
- Positive indicators
- Negative indicators
- Strong positive indicators
- Strong negative indicators
- Username presence
- Redirect behavior
- Response fingerprints
- Confidence scores
- Request timing
- Rate-limit responses

Results are classified into:

```text
FOUND
NOT_FOUND
UNCERTAIN
UNKNOWN
RATE_LIMITED
ERROR
````

This helps reduce false positives caused by generic pages, redirects, custom error pages, and anti-bot systems.

---

## 🧬 Username Variation Engine

SHENWIN can generate additional username candidates from a base username.

Examples:

```text
username
username1
username01
username99
1username
username_x
username_
username-
theusername
realusername
officialusername
iamusername
username_irl
username_pro
username_yt
username2025
```

It also supports:

* Numeric variations
* Prefixes
* Suffixes
* Separator variations
* Turkish character normalization
* ASCII conversion
* Leetspeak transformations
* Repeated-character variations

Example:

```text
miraç
mirac
m1rac
m1r4c
mirac1
realmiraç
miraç_irl
```

---

## 🎯 Confidence Scoring

Every result receives a confidence score based on multiple pieces of evidence.

Example:

```text
FOUND
Confidence: HIGH
Score: 87

Evidence:
  + Profile-like response
  + Username detected in response
  + Positive platform marker
  + Valid HTTP response
  + Canonical-looking URL
```

Instead of relying only on:

```text
HTTP 200 = FOUND
```

SHENWIN evaluates several indicators before deciding whether a result is likely to be a real profile.

---

## 🌐 Response Fingerprinting

SHENWIN analyzes responses to help distinguish real profiles from generic pages.

Fingerprinting can use:

* Response size
* Page title
* Content markers
* Response structure
* HTTP status
* Redirect destination
* Username presence

This provides a stronger signal when platforms return successful HTTP responses for both existing and non-existing users.

---

## 🔀 Redirect Analysis

SHENWIN tracks the final destination of requests.

This helps identify situations such as:

```text
username page
      ↓
redirect
      ↓
login page
```

or:

```text
username page
      ↓
redirect
      ↓
generic 404 page
```

Redirect information is included in result data where available.

---

## 🛡️ Rate-Limit Awareness

SHENWIN recognizes common rate-limit and temporary failure responses.

Examples:

```text
HTTP 429
HTTP 502
HTTP 503
HTTP 504
```

The scanner can retry temporary failures using controlled retry attempts and backoff behavior.

It does not attempt to bypass platform rate limits.

---

## ⚡ Concurrent Scanning

SHENWIN uses bounded concurrency to improve scanning speed without creating an uncontrolled number of threads.

Example:

```text
Workers: 12
Platforms: 400+
```

Configure workers:

```bash
python3 shenwin.py targetuser --workers 20
```

Add a delay between requests:

```bash
python3 shenwin.py targetuser --delay 0.2
```

---

## 🔁 Retry & Timeout Control

HTTP requests support configurable:

* Timeout
* Retry count
* Backoff
* Request delay
* Worker count

Example:

```bash
python3 shenwin.py targetuser \
    --timeout 10 \
    --retries 3 \
    --workers 16 \
    --delay 0.2
```

---

## 💾 Result Export

SHENWIN supports structured result formats.

### JSON

```bash
python3 shenwin.py targetuser \
    --format json \
    -o results.json
```

### CSV

```bash
python3 shenwin.py targetuser \
    --format csv \
    -o results.csv
```

### TXT

```bash
python3 shenwin.py targetuser \
    --format txt \
    -o results.txt
```

### HTML

```bash
python3 shenwin.py targetuser \
    --html report.html
```

HTML reports provide a readable overview of scan results.

---

## 📊 Baseline & Comparison

SHENWIN can save scan results as a baseline.

```bash
python3 shenwin.py targetuser \
    --save-baseline baseline.json
```

A later scan can be compared against the baseline:

```bash
python3 shenwin.py targetuser \
    --compare baseline.json
```

This makes it possible to identify changes between scans.

Example:

```text
NEW
  GitHub
  Reddit

REMOVED
  ExamplePlatform

CHANGED
  ExampleSite
```

---

## 🎛️ Platform Filtering

Scan specific platforms:

```bash
python3 shenwin.py targetuser \
    -p github \
    -p reddit
```

Filter by category:

```bash
python3 shenwin.py targetuser \
    -c Development
```

Exclude platforms:

```bash
python3 shenwin.py targetuser \
    --exclude Instagram \
    --exclude TikTok
```

List available platforms:

```bash
python3 shenwin.py --list-platforms
```

---

## 📂 Username Lists

SHENWIN can scan multiple usernames from a file.

Example:

```text
miraç
mirac
laxent
latent
cybermiraç
```

Run:

```bash
python3 shenwin.py \
    -f usernames.txt \
    -o results.json \
    --format json
```

---

# 🐰 Terminal Interface

SHENWIN includes a terminal-oriented interface with:

```text
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ███████╗██╗  ██╗███████╗███╗   ██╗██╗    ██╗██╗███╗   ██╗ ║
║   ██╔════╝██║  ██║██╔════╝████╗  ██║██║    ██║██║████╗  ██║ ║
║   ███████╗███████║█████╗  ██╔██╗ ██║██║ █╗ ██║██║██╔██╗ ██║ ║
║   ╚════██║██╔══██║██╔══╝  ██║╚██╗██║██║███╗██║██║██║╚██╗██║ ║
║   ███████║██║  ██║███████╗██║ ╚████║╚███╔███╔╝██║██║ ╚████║ ║
║   ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝ ╚══╝╚══╝ ╚═╝╚═╝  ╚═══╝ ║
║                                                              ║
║   OSINT Username Enumeration & Correlation Tool              ║
╚══════════════════════════════════════════════════════════════╝
```

The interface provides:

* Colored status output
* Scan progress
* Spinner
* Platform statistics
* Confidence information
* Detection evidence
* Timing information
* Error and rate-limit information

Disable colors when required:

```bash
python3 shenwin.py targetuser --no-color
```

---

# 🔬 Scan Workflow

A typical SHENWIN scan follows this workflow:

```text
                ┌─────────────────┐
                │    Username     │
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │ Input Validation│
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │ Platform Filter │
                └────────┬────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │ Concurrent HTTP Scan │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │ Response Analysis    │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │ Fingerprint Analysis │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │ Confidence Scoring   │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │ Structured Results   │
              └──────────────────────┘
```

---

# 🧩 Scan Modes

## Standard Scan

Search the username across the platform database:

```bash
python3 shenwin.py targetuser
```

## Platform Scan

Scan selected platforms:

```bash
python3 shenwin.py targetuser \
    -p github \
    -p reddit \
    -p gitlab
```

## Category Scan

Focus on a specific platform category:

```bash
python3 shenwin.py targetuser \
    -c Development
```

## Variation Scan

Generate and scan username variations:

```bash
python3 shenwin.py targetuser \
    --variations
```

## Single Platform

Test a specific service:

```bash
python3 shenwin.py targetuser \
    -p github
```

---

# 🗂️ Platform Categories

SHENWIN organizes services into categories including:

```text
Social
Development
Cybersecurity
Gaming
Music
Video
Photography
Art
Writing
Forums
Education
Professional
Identity
Monetization
Sports
Travel
Marketplace
Books & Media
Crypto / Web3
Wiki
```

---

# 🧪 Example Output

```text
🐰 SHENWIN

Target     : LaxenT
Platforms  : 400+
Workers    : 12

[✓] GitHub
    https://github.com/LaxenT
    Confidence: HIGH
    Score: 91

[✓] Reddit
    https://www.reddit.com/user/LaxenT
    Confidence: MEDIUM
    Score: 58

[?] ExamplePlatform
    Confidence: LOW
    Score: 27
    Reason: Generic response detected

[×] ExampleSite
    HTTP 404
    NOT_FOUND

[!] ExamplePlatform
    RATE_LIMITED
```

---

# 🛠️ Installation

## Linux / macOS

```bash
git clone https://github.com/LaxenTgit/shenwin.git
cd shenwin
python3 shenwin.py targetuser
```

Optional global installation:

```bash
chmod +x shenwin.py
sudo cp shenwin.py /usr/local/bin/shenwin
```

Then:

```bash
shenwin targetuser
```

## Windows

Install Python:

```powershell
winget install Python.Python.3.11
```

Clone the repository:

```powershell
git clone https://github.com/LaxenTgit/shenwin.git
cd shenwin
```

Run:

```powershell
python shenwin.py targetuser
```

---

# 📦 Dependencies

SHENWIN is designed around the Python standard library.

Core components include:

```text
urllib
argparse
concurrent.futures
threading
json
csv
hashlib
re
time
datetime
```

No third-party Python packages are required for the core scanner.

---

# 🖥️ Compatibility

```text
Linux
macOS
Windows
```

Python:

```text
Python 3.8+
```

---

# 🔐 Responsible Use

SHENWIN is intended for:

* Authorized security research
* OSINT investigations
* CTF environments
* Bug bounty reconnaissance
* Username discovery
* Digital footprint research
* Security education

Only scan usernames and services where you have appropriate authorization or where the activity is consistent with the service's terms and applicable law.

SHENWIN does not attempt to:

* Bypass authentication
* Guess passwords
* Take over accounts
* Circumvent access controls
* Bypass rate limits
* Exploit vulnerabilities

The tool performs public-facing username enumeration and response analysis.

---

# 🚀 Roadmap

## v2.1 — Accuracy

* Platform-specific checkers
* Better false-positive detection
* Canonical URL detection
* Redirect-chain analysis
* Improved response fingerprints
* Stronger evidence scoring
* Platform-specific negative markers
* Metadata extraction

## v2.2 — Performance

* Host-level throttling
* Persistent HTTP sessions
* Smarter retry strategy
* Response caching
* Live progress dashboard
* Platform health detection
* Improved concurrency

## v2.3 — Intelligence

* Cross-platform username correlation
* Username similarity analysis
* Profile metadata correlation
* Avatar hash / perceptual hash comparison
* Historical profile changes
* Username monitoring
* Identity-confidence scoring

## v3.0 — Architecture

```text
Scanner Engine
      │
      ├── Platform Database
      │
      ├── Checker Engine
      │
      ├── Fingerprint Engine
      │
      ├── Correlation Engine
      │
      ├── Cache
      │
      ├── SQLite Storage
      │
      ├── Monitoring
      │
      └── Reporting
```

Planned architecture improvements include:

* Modular platform checkers
* External platform database
* SQLite result storage
* Plugin support
* Monitoring mode
* Advanced correlation
* Graph-based relationship analysis
* Improved reporting

---

# 📈 Why SHENWIN?

Traditional username scanners often depend heavily on a simple model:

```text
HTTP 200
   ↓
FOUND
```

SHENWIN aims to move toward:

```text
HTTP Response
      ↓
Content Analysis
      ↓
Fingerprinting
      ↓
Platform Indicators
      ↓
Redirect Analysis
      ↓
Evidence Collection
      ↓
Confidence Score
      ↓
FOUND / NOT_FOUND / UNCERTAIN
```

This makes the scanner more useful for real OSINT workflows where false positives and platform-specific behavior matter.

---

# 🐰 SHENWIN

**OSINT Username Enumeration & Correlation**

Built with Python.

Made for reconnaissance, research, and security.

```text
Search smarter.
Verify better.
Correlate responsibly.
```
```
```
