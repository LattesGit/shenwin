# 🐰 SHENWIN OSINT Username Enumeration Tool
🐰 Python OSINT tool for username enumeration across 500+ platforms with variation engine (sherlock + winget)

> Fast username enumeration across 400+ platforms. Pure Python, zero dependencies.

[![GitHub stars](https://img.shields.io/github/stars/kullaniciadi/shenwin?style=social)](https://github.com/kullaniciadi/shenwin)
[![GitHub forks](https://img.shields.io/github/forks/kullaniciadi/shenwin)](https://github.com/kullaniciadi/shenwin)
[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/)

## Features

- **400+ platforms** — Social, dev, gaming, forums, crypto, more
- **5 scan modes** — Single username, variations, recon-only, list-only, single-site
- **Variation engine** — Leetspeak, numbers, prefixes/suffixes, ASCII conversion
- **Multi-threaded** — Parallel HTTP checks (50+ threads)
- **Winget integration** — Windows package manager for OSINT tools
- **Zero dependencies** — Stdlib only (Python 3.6+)
- **JSON/CSV export** — Structured results
- **Cross-platform** — Linux/Mac/Windows

## Installation

```bash
# Clone & run
git clone https://github.com/LaxenTgit/shenwin
cd shenwin
python3 shenwin.py -w targetuser

# Global install (Linux/Mac)
chmod +x shenwin.py
sudo cp shenwin.py /usr/local/bin/shenwin

# Windows (PowerShell)
winget install Python.Python.3.11
python shenwin.py -w targetuser

## What's shenwin
# shenwin

Shenwin is a Python-based OSINT username enumeration tool inspired by Sherlock and other reconnaissance utilities. It is designed to unify multiple OSINT approaches into a single workflow, enabling broader and faster username discovery across online platforms.

The tool checks username availability and presence across a large number of services while also extending search coverage through username variation generation. These variations include prefixes, suffixes, numeric patterns, and leetspeak transformations, allowing deeper reconnaissance beyond a single static username query.

Shenwin can also integrate OSINT tooling workflows on Windows environments via Winget support, making it more adaptable for multi-platform reconnaissance setups. Its multi-threaded architecture improves performance by running parallel checks across many services simultaneously.

The main goal of Shenwin is to enhance username-based OSINT investigations by combining enumeration, variation generation, and multi-source verification into a single lightweight Python tool.

In summary, Shenwin provides a unified and extensible approach to username reconnaissance, improving both coverage and efficiency in OSINT operations.
