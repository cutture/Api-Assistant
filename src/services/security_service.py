"""
Security Scanner Service for code vulnerability detection.

Provides security scanning capabilities using multiple backends:
- Bandit for Python code analysis
- npm audit / Snyk for JavaScript/TypeScript
- Static pattern matching for common vulnerabilities
"""

import asyncio
import json
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

from src.config import settings


class Severity(str, Enum):
    """Vulnerability severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VulnerabilityType(str, Enum):
    """Types of security vulnerabilities."""
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    HARDCODED_SECRET = "hardcoded_secret"
    INSECURE_DESERIALIZATION = "insecure_deserialization"
    INSECURE_RANDOM = "insecure_random"
    WEAK_CRYPTO = "weak_crypto"
    INSECURE_SSL = "insecure_ssl"
    DEPENDENCY_VULNERABILITY = "dependency_vulnerability"
    SENSITIVE_DATA_EXPOSURE = "sensitive_data_exposure"
    INSECURE_PERMISSIONS = "insecure_permissions"
    BUFFER_OVERFLOW = "buffer_overflow"
    OTHER = "other"


@dataclass
class Vulnerability:
    """Represents a security vulnerability found in code."""
    type: VulnerabilityType
    severity: Severity
    message: str
    line: Optional[int] = None
    column: Optional[int] = None
    code_snippet: Optional[str] = None
    fix_suggestion: Optional[str] = None
    cwe_id: Optional[str] = None
    owasp_category: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "severity": self.severity.value,
            "message": self.message,
            "line": self.line,
            "column": self.column,
            "code_snippet": self.code_snippet,
            "fix_suggestion": self.fix_suggestion,
            "cwe_id": self.cwe_id,
            "owasp_category": self.owasp_category,
        }


@dataclass
class SecurityScanResult:
    """Result of a security scan."""
    passed: bool
    vulnerabilities: list[Vulnerability] = field(default_factory=list)
    risk_score: int = 0  # 0-100, higher is worse
    scan_duration_ms: int = 0
    scanner_used: str = "pattern_matcher"
    blocked: bool = False  # True if high-severity found and blocking enabled
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "vulnerabilities": [v.to_dict() for v in self.vulnerabilities],
            "risk_score": self.risk_score,
            "scan_duration_ms": self.scan_duration_ms,
            "scanner_used": self.scanner_used,
            "blocked": self.blocked,
            "summary": self.summary,
            "counts": {
                "critical": sum(1 for v in self.vulnerabilities if v.severity == Severity.CRITICAL),
                "high": sum(1 for v in self.vulnerabilities if v.severity == Severity.HIGH),
                "medium": sum(1 for v in self.vulnerabilities if v.severity == Severity.MEDIUM),
                "low": sum(1 for v in self.vulnerabilities if v.severity == Severity.LOW),
                "info": sum(1 for v in self.vulnerabilities if v.severity == Severity.INFO),
            }
        }


# Security patterns for static analysis
SECURITY_PATTERNS = {
    "python": [
        # SQL Injection
        {
            "pattern": r'execute\s*\(\s*["\'].*%s.*["\']\s*%',
            "type": VulnerabilityType.SQL_INJECTION,
            "severity": Severity.HIGH,
            "message": "Potential SQL injection via string formatting",
            "fix": "Use parameterized queries instead of string formatting",
            "cwe": "CWE-89",
            "owasp": "A03:2021-Injection",
        },
        {
            "pattern": r'execute\s*\(\s*f["\']',
            "type": VulnerabilityType.SQL_INJECTION,
            "severity": Severity.HIGH,
            "message": "Potential SQL injection via f-string",
            "fix": "Use parameterized queries instead of f-strings",
            "cwe": "CWE-89",
            "owasp": "A03:2021-Injection",
        },
        # Command Injection
        {
            "pattern": r'os\.system\s*\(',
            "type": VulnerabilityType.COMMAND_INJECTION,
            "severity": Severity.HIGH,
            "message": "Use of os.system() is vulnerable to command injection",
            "fix": "Use subprocess.run() with shell=False and a list of arguments",
            "cwe": "CWE-78",
            "owasp": "A03:2021-Injection",
        },
        {
            "pattern": r'subprocess\.(call|run|Popen)\s*\([^)]*shell\s*=\s*True',
            "type": VulnerabilityType.COMMAND_INJECTION,
            "severity": Severity.HIGH,
            "message": "shell=True in subprocess is vulnerable to command injection",
            "fix": "Use shell=False and pass command as a list",
            "cwe": "CWE-78",
            "owasp": "A03:2021-Injection",
        },
        {
            "pattern": r'eval\s*\(',
            "type": VulnerabilityType.COMMAND_INJECTION,
            "severity": Severity.CRITICAL,
            "message": "Use of eval() allows arbitrary code execution",
            "fix": "Avoid eval(); use ast.literal_eval() for safe literal parsing",
            "cwe": "CWE-95",
            "owasp": "A03:2021-Injection",
        },
        {
            "pattern": r'exec\s*\(',
            "type": VulnerabilityType.COMMAND_INJECTION,
            "severity": Severity.CRITICAL,
            "message": "Use of exec() allows arbitrary code execution",
            "fix": "Avoid exec(); redesign to avoid dynamic code execution",
            "cwe": "CWE-95",
            "owasp": "A03:2021-Injection",
        },
        # Hardcoded Secrets
        {
            "pattern": r'(password|passwd|pwd|secret|api_key|apikey|token|auth)\s*=\s*["\'][^"\']{8,}["\']',
            "type": VulnerabilityType.HARDCODED_SECRET,
            "severity": Severity.HIGH,
            "message": "Hardcoded secret detected",
            "fix": "Use environment variables or a secrets manager",
            "cwe": "CWE-798",
            "owasp": "A07:2021-Identification and Authentication Failures",
        },
        # Insecure Deserialization
        {
            "pattern": r'pickle\.loads?\s*\(',
            "type": VulnerabilityType.INSECURE_DESERIALIZATION,
            "severity": Severity.HIGH,
            "message": "Pickle deserialization can execute arbitrary code",
            "fix": "Use JSON or other safe serialization formats",
            "cwe": "CWE-502",
            "owasp": "A08:2021-Software and Data Integrity Failures",
        },
        {
            "pattern": r'yaml\.load\s*\([^)]*\)',
            "type": VulnerabilityType.INSECURE_DESERIALIZATION,
            "severity": Severity.MEDIUM,
            "message": "yaml.load() is unsafe; use yaml.safe_load()",
            "fix": "Replace yaml.load() with yaml.safe_load()",
            "cwe": "CWE-502",
            "owasp": "A08:2021-Software and Data Integrity Failures",
        },
        # Insecure Random
        {
            "pattern": r'random\.(random|randint|choice|shuffle)\s*\(',
            "type": VulnerabilityType.INSECURE_RANDOM,
            "severity": Severity.MEDIUM,
            "message": "random module is not cryptographically secure",
            "fix": "Use secrets module for security-sensitive random values",
            "cwe": "CWE-330",
            "owasp": "A02:2021-Cryptographic Failures",
        },
        # Weak Crypto
        {
            "pattern": r'(md5|sha1)\s*\(',
            "type": VulnerabilityType.WEAK_CRYPTO,
            "severity": Severity.MEDIUM,
            "message": "MD5/SHA1 are weak hash algorithms",
            "fix": "Use SHA-256 or stronger hash algorithms",
            "cwe": "CWE-328",
            "owasp": "A02:2021-Cryptographic Failures",
        },
        {
            "pattern": r'DES|Blowfish|RC4',
            "type": VulnerabilityType.WEAK_CRYPTO,
            "severity": Severity.HIGH,
            "message": "Weak encryption algorithm detected",
            "fix": "Use AES-256-GCM or ChaCha20-Poly1305",
            "cwe": "CWE-327",
            "owasp": "A02:2021-Cryptographic Failures",
        },
        # SSL/TLS Issues
        {
            "pattern": r'verify\s*=\s*False',
            "type": VulnerabilityType.INSECURE_SSL,
            "severity": Severity.HIGH,
            "message": "SSL certificate verification disabled",
            "fix": "Enable SSL certificate verification",
            "cwe": "CWE-295",
            "owasp": "A07:2021-Identification and Authentication Failures",
        },
        # Path Traversal
        {
            "pattern": r'open\s*\([^)]*\+[^)]*\)',
            "type": VulnerabilityType.PATH_TRAVERSAL,
            "severity": Severity.MEDIUM,
            "message": "Potential path traversal via string concatenation",
            "fix": "Validate and sanitize file paths; use pathlib",
            "cwe": "CWE-22",
            "owasp": "A01:2021-Broken Access Control",
        },
    ],
    "javascript": [
        # XSS
        {
            "pattern": r'innerHTML\s*=',
            "type": VulnerabilityType.XSS,
            "severity": Severity.HIGH,
            "message": "innerHTML assignment can lead to XSS",
            "fix": "Use textContent or sanitize HTML with DOMPurify",
            "cwe": "CWE-79",
            "owasp": "A03:2021-Injection",
        },
        {
            "pattern": r'document\.write\s*\(',
            "type": VulnerabilityType.XSS,
            "severity": Severity.HIGH,
            "message": "document.write() can lead to XSS",
            "fix": "Use DOM manipulation methods instead",
            "cwe": "CWE-79",
            "owasp": "A03:2021-Injection",
        },
        {
            "pattern": r'dangerouslySetInnerHTML',
            "type": VulnerabilityType.XSS,
            "severity": Severity.MEDIUM,
            "message": "dangerouslySetInnerHTML can lead to XSS if input not sanitized",
            "fix": "Sanitize HTML with DOMPurify before using",
            "cwe": "CWE-79",
            "owasp": "A03:2021-Injection",
        },
        # SQL Injection
        {
            "pattern": r'query\s*\(\s*[`"\'].*\$\{',
            "type": VulnerabilityType.SQL_INJECTION,
            "severity": Severity.HIGH,
            "message": "Potential SQL injection via template literal",
            "fix": "Use parameterized queries",
            "cwe": "CWE-89",
            "owasp": "A03:2021-Injection",
        },
        # Command Injection
        {
            "pattern": r'exec\s*\(',
            "type": VulnerabilityType.COMMAND_INJECTION,
            "severity": Severity.CRITICAL,
            "message": "child_process.exec() is vulnerable to command injection",
            "fix": "Use execFile() with arguments as array",
            "cwe": "CWE-78",
            "owasp": "A03:2021-Injection",
        },
        {
            "pattern": r'eval\s*\(',
            "type": VulnerabilityType.COMMAND_INJECTION,
            "severity": Severity.CRITICAL,
            "message": "eval() allows arbitrary code execution",
            "fix": "Avoid eval(); use JSON.parse() for data parsing",
            "cwe": "CWE-95",
            "owasp": "A03:2021-Injection",
        },
        # Hardcoded Secrets
        {
            "pattern": r'(password|secret|api_key|apiKey|token|auth)\s*[:=]\s*["\'][^"\']{8,}["\']',
            "type": VulnerabilityType.HARDCODED_SECRET,
            "severity": Severity.HIGH,
            "message": "Hardcoded secret detected",
            "fix": "Use environment variables",
            "cwe": "CWE-798",
            "owasp": "A07:2021-Identification and Authentication Failures",
        },
        # Insecure Random
        {
            "pattern": r'Math\.random\s*\(',
            "type": VulnerabilityType.INSECURE_RANDOM,
            "severity": Severity.MEDIUM,
            "message": "Math.random() is not cryptographically secure",
            "fix": "Use crypto.getRandomValues() or crypto.randomBytes()",
            "cwe": "CWE-330",
            "owasp": "A02:2021-Cryptographic Failures",
        },
        # Prototype Pollution
        {
            "pattern": r'__proto__|prototype\s*\[',
            "type": VulnerabilityType.OTHER,
            "severity": Severity.HIGH,
            "message": "Potential prototype pollution",
            "fix": "Use Object.create(null) or validate property names",
            "cwe": "CWE-1321",
            "owasp": "A03:2021-Injection",
        },
    ],
    "typescript": [],  # Will inherit from javascript
    "java": [
        # SQL Injection
        {
            "pattern": r'Statement.*execute.*\+',
            "type": VulnerabilityType.SQL_INJECTION,
            "severity": Severity.HIGH,
            "message": "Potential SQL injection via string concatenation",
            "fix": "Use PreparedStatement with parameterized queries",
            "cwe": "CWE-89",
            "owasp": "A03:2021-Injection",
        },
        # Command Injection
        {
            "pattern": r'Runtime\.getRuntime\(\)\.exec\s*\(',
            "type": VulnerabilityType.COMMAND_INJECTION,
            "severity": Severity.HIGH,
            "message": "Runtime.exec() is vulnerable to command injection",
            "fix": "Use ProcessBuilder with argument list",
            "cwe": "CWE-78",
            "owasp": "A03:2021-Injection",
        },
        # Insecure Deserialization
        {
            "pattern": r'ObjectInputStream.*readObject\s*\(',
            "type": VulnerabilityType.INSECURE_DESERIALIZATION,
            "severity": Severity.CRITICAL,
            "message": "Unsafe deserialization of untrusted data",
            "fix": "Implement ObjectInputFilter or use safe serialization",
            "cwe": "CWE-502",
            "owasp": "A08:2021-Software and Data Integrity Failures",
        },
        # Weak Crypto
        {
            "pattern": r'Cipher\.getInstance\s*\(\s*["\']DES',
            "type": VulnerabilityType.WEAK_CRYPTO,
            "severity": Severity.HIGH,
            "message": "DES is a weak encryption algorithm",
            "fix": "Use AES/GCM/NoPadding",
            "cwe": "CWE-327",
            "owasp": "A02:2021-Cryptographic Failures",
        },
        # XXE
        {
            "pattern": r'DocumentBuilderFactory|SAXParserFactory|XMLInputFactory',
            "type": VulnerabilityType.OTHER,
            "severity": Severity.MEDIUM,
            "message": "XML parser may be vulnerable to XXE",
            "fix": "Disable external entities and DTDs",
            "cwe": "CWE-611",
            "owasp": "A05:2021-Security Misconfiguration",
        },
    ],
    "go": [
        # SQL Injection
        {
            "pattern": r'db\.(Query|Exec)\s*\([^,]*\+',
            "type": VulnerabilityType.SQL_INJECTION,
            "severity": Severity.HIGH,
            "message": "Potential SQL injection via string concatenation",
            "fix": "Use parameterized queries with ?",
            "cwe": "CWE-89",
            "owasp": "A03:2021-Injection",
        },
        # Command Injection
        {
            "pattern": r'exec\.Command\s*\(\s*["\']sh["\'],\s*["\']-c["\']',
            "type": VulnerabilityType.COMMAND_INJECTION,
            "severity": Severity.HIGH,
            "message": "Shell command execution is vulnerable to injection",
            "fix": "Pass command and arguments separately to exec.Command()",
            "cwe": "CWE-78",
            "owasp": "A03:2021-Injection",
        },
        # Hardcoded Secrets
        {
            "pattern": r'(password|secret|apiKey|token)\s*:?=\s*["`][^"`]{8,}["`]',
            "type": VulnerabilityType.HARDCODED_SECRET,
            "severity": Severity.HIGH,
            "message": "Hardcoded secret detected",
            "fix": "Use environment variables or a secrets manager",
            "cwe": "CWE-798",
            "owasp": "A07:2021-Identification and Authentication Failures",
        },
        # Insecure TLS
        {
            "pattern": r'InsecureSkipVerify:\s*true',
            "type": VulnerabilityType.INSECURE_SSL,
            "severity": Severity.HIGH,
            "message": "TLS certificate verification disabled",
            "fix": "Enable certificate verification",
            "cwe": "CWE-295",
            "owasp": "A07:2021-Identification and Authentication Failures",
        },
    ],
    "csharp": [
        # SQL Injection
        {
            "pattern": r'SqlCommand.*\+',
            "type": VulnerabilityType.SQL_INJECTION,
            "severity": Severity.HIGH,
            "message": "Potential SQL injection via string concatenation",
            "fix": "Use SqlParameter for parameterized queries",
            "cwe": "CWE-89",
            "owasp": "A03:2021-Injection",
        },
        # Command Injection
        {
            "pattern": r'Process\.Start\s*\(',
            "type": VulnerabilityType.COMMAND_INJECTION,
            "severity": Severity.MEDIUM,
            "message": "Process.Start() may be vulnerable to injection",
            "fix": "Validate and sanitize all input",
            "cwe": "CWE-78",
            "owasp": "A03:2021-Injection",
        },
        # Insecure Deserialization
        {
            "pattern": r'BinaryFormatter|ObjectStateFormatter',
            "type": VulnerabilityType.INSECURE_DESERIALIZATION,
            "severity": Severity.CRITICAL,
            "message": "BinaryFormatter is insecure for untrusted data",
            "fix": "Use System.Text.Json or validated serializers",
            "cwe": "CWE-502",
            "owasp": "A08:2021-Software and Data Integrity Failures",
        },
        # Weak Crypto
        {
            "pattern": r'MD5|SHA1|DES',
            "type": VulnerabilityType.WEAK_CRYPTO,
            "severity": Severity.MEDIUM,
            "message": "Weak cryptographic algorithm detected",
            "fix": "Use SHA-256 or AES-256",
            "cwe": "CWE-327",
            "owasp": "A02:2021-Cryptographic Failures",
        },
    ],
}

# TypeScript inherits JavaScript patterns
SECURITY_PATTERNS["typescript"] = SECURITY_PATTERNS["javascript"].copy()


class SecurityService:
    """Service for scanning code for security vulnerabilities."""

    def __init__(self):
        self.block_high_severity = getattr(settings, 'BLOCK_HIGH_SEVERITY', True)
        self.snyk_api_key = getattr(settings, 'SNYK_API_KEY', None)

    async def scan_code(
        self,
        code: str,
        language: str,
        filename: Optional[str] = None,
    ) -> SecurityScanResult:
        """
        Scan code for security vulnerabilities.

        Args:
            code: The source code to scan
            language: Programming language (python, javascript, typescript, java, go, csharp)
            filename: Optional filename for better context

        Returns:
            SecurityScanResult with vulnerabilities found
        """
        import time
        start_time = time.time()

        vulnerabilities = []
        scanner_used = "pattern_matcher"

        # Normalize language
        lang = language.lower()
        if lang in ("js", "jsx"):
            lang = "javascript"
        elif lang in ("ts", "tsx"):
            lang = "typescript"
        elif lang in ("py",):
            lang = "python"
        elif lang in ("cs",):
            lang = "csharp"

        # Run pattern-based scanning
        pattern_vulns = self._scan_with_patterns(code, lang)
        vulnerabilities.extend(pattern_vulns)

        # Try to run Bandit for Python
        if lang == "python":
            try:
                bandit_vulns = await self._run_bandit(code)
                vulnerabilities.extend(bandit_vulns)
                scanner_used = "bandit+patterns"
            except Exception:
                pass  # Fall back to patterns only

        # Calculate risk score
        risk_score = self._calculate_risk_score(vulnerabilities)

        # Check if should block
        has_critical_or_high = any(
            v.severity in (Severity.CRITICAL, Severity.HIGH)
            for v in vulnerabilities
        )
        blocked = self.block_high_severity and has_critical_or_high

        # Determine if passed
        passed = not has_critical_or_high

        # Generate summary
        summary = self._generate_summary(vulnerabilities)

        scan_duration_ms = int((time.time() - start_time) * 1000)

        return SecurityScanResult(
            passed=passed,
            vulnerabilities=vulnerabilities,
            risk_score=risk_score,
            scan_duration_ms=scan_duration_ms,
            scanner_used=scanner_used,
            blocked=blocked,
            summary=summary,
        )

    def _scan_with_patterns(self, code: str, language: str) -> list[Vulnerability]:
        """Scan code using regex patterns."""
        vulnerabilities = []
        patterns = SECURITY_PATTERNS.get(language, [])

        lines = code.split('\n')

        for pattern_def in patterns:
            pattern = pattern_def["pattern"]
            regex = re.compile(pattern, re.IGNORECASE)

            for line_num, line in enumerate(lines, 1):
                matches = regex.finditer(line)
                for match in matches:
                    vuln = Vulnerability(
                        type=pattern_def["type"],
                        severity=pattern_def["severity"],
                        message=pattern_def["message"],
                        line=line_num,
                        column=match.start() + 1,
                        code_snippet=line.strip()[:100],
                        fix_suggestion=pattern_def.get("fix"),
                        cwe_id=pattern_def.get("cwe"),
                        owasp_category=pattern_def.get("owasp"),
                    )
                    vulnerabilities.append(vuln)

        return vulnerabilities

    async def _run_bandit(self, code: str) -> list[Vulnerability]:
        """Run Bandit security scanner on Python code."""
        vulnerabilities = []

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            result = await asyncio.create_subprocess_exec(
                'bandit',
                '-f', 'json',
                '-q',
                temp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(result.communicate(), timeout=30)

            if stdout:
                try:
                    data = json.loads(stdout.decode())
                    for issue in data.get('results', []):
                        severity_map = {
                            'HIGH': Severity.HIGH,
                            'MEDIUM': Severity.MEDIUM,
                            'LOW': Severity.LOW,
                        }
                        vuln = Vulnerability(
                            type=VulnerabilityType.OTHER,
                            severity=severity_map.get(issue.get('issue_severity', 'LOW'), Severity.LOW),
                            message=issue.get('issue_text', ''),
                            line=issue.get('line_number'),
                            code_snippet=issue.get('code', '')[:100],
                            cwe_id=issue.get('issue_cwe', {}).get('id'),
                        )
                        vulnerabilities.append(vuln)
                except json.JSONDecodeError:
                    pass
        except (asyncio.TimeoutError, FileNotFoundError):
            pass
        finally:
            Path(temp_path).unlink(missing_ok=True)

        return vulnerabilities

    def _calculate_risk_score(self, vulnerabilities: list[Vulnerability]) -> int:
        """Calculate overall risk score (0-100)."""
        if not vulnerabilities:
            return 0

        score = 0
        severity_weights = {
            Severity.CRITICAL: 25,
            Severity.HIGH: 15,
            Severity.MEDIUM: 8,
            Severity.LOW: 3,
            Severity.INFO: 1,
        }

        for vuln in vulnerabilities:
            score += severity_weights.get(vuln.severity, 1)

        # Cap at 100
        return min(100, score)

    def _generate_summary(self, vulnerabilities: list[Vulnerability]) -> str:
        """Generate a human-readable summary of findings."""
        if not vulnerabilities:
            return "No security vulnerabilities detected."

        counts = {}
        for vuln in vulnerabilities:
            counts[vuln.severity] = counts.get(vuln.severity, 0) + 1

        parts = []
        for severity in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INFO]:
            if severity in counts:
                parts.append(f"{counts[severity]} {severity.value}")

        total = len(vulnerabilities)
        return f"Found {total} issue(s): {', '.join(parts)}"

    async def scan_dependencies(
        self,
        package_file: str,
        package_type: str,  # "pip", "npm", "cargo", etc.
    ) -> SecurityScanResult:
        """
        Scan dependencies for known vulnerabilities.

        Args:
            package_file: Contents of package file (requirements.txt, package.json, etc.)
            package_type: Type of package manager

        Returns:
            SecurityScanResult with dependency vulnerabilities
        """
        import time
        start_time = time.time()

        vulnerabilities = []
        scanner_used = "dependency_check"

        if package_type == "npm" and package_file:
            vulnerabilities = await self._check_npm_audit(package_file)
        elif package_type == "pip" and package_file:
            vulnerabilities = await self._check_pip_audit(package_file)

        risk_score = self._calculate_risk_score(vulnerabilities)
        has_critical_or_high = any(
            v.severity in (Severity.CRITICAL, Severity.HIGH)
            for v in vulnerabilities
        )

        scan_duration_ms = int((time.time() - start_time) * 1000)

        return SecurityScanResult(
            passed=not has_critical_or_high,
            vulnerabilities=vulnerabilities,
            risk_score=risk_score,
            scan_duration_ms=scan_duration_ms,
            scanner_used=scanner_used,
            blocked=self.block_high_severity and has_critical_or_high,
            summary=self._generate_summary(vulnerabilities),
        )

    async def _check_npm_audit(self, package_json: str) -> list[Vulnerability]:
        """Run npm audit on package.json."""
        vulnerabilities = []

        with tempfile.TemporaryDirectory() as tmpdir:
            package_path = Path(tmpdir) / "package.json"
            package_path.write_text(package_json)

            try:
                result = await asyncio.create_subprocess_exec(
                    'npm', 'audit', '--json',
                    cwd=tmpdir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, _ = await asyncio.wait_for(result.communicate(), timeout=60)

                if stdout:
                    data = json.loads(stdout.decode())
                    for advisory in data.get('advisories', {}).values():
                        severity_map = {
                            'critical': Severity.CRITICAL,
                            'high': Severity.HIGH,
                            'moderate': Severity.MEDIUM,
                            'low': Severity.LOW,
                        }
                        vuln = Vulnerability(
                            type=VulnerabilityType.DEPENDENCY_VULNERABILITY,
                            severity=severity_map.get(advisory.get('severity', 'low'), Severity.LOW),
                            message=f"{advisory.get('module_name')}: {advisory.get('title')}",
                            fix_suggestion=advisory.get('recommendation'),
                            cwe_id=advisory.get('cwe'),
                        )
                        vulnerabilities.append(vuln)
            except (asyncio.TimeoutError, FileNotFoundError, json.JSONDecodeError):
                pass

        return vulnerabilities

    async def _check_pip_audit(self, requirements: str) -> list[Vulnerability]:
        """Check Python dependencies for vulnerabilities using pip-audit."""
        vulnerabilities = []

        with tempfile.TemporaryDirectory() as tmpdir:
            req_path = Path(tmpdir) / "requirements.txt"
            req_path.write_text(requirements)

            try:
                result = await asyncio.create_subprocess_exec(
                    'pip-audit',
                    '--requirement', str(req_path),
                    '--format', 'json',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, _ = await asyncio.wait_for(result.communicate(), timeout=120)

                if stdout:
                    data = json.loads(stdout.decode())
                    for vuln_data in data:
                        vuln = Vulnerability(
                            type=VulnerabilityType.DEPENDENCY_VULNERABILITY,
                            severity=Severity.HIGH,  # pip-audit doesn't provide severity
                            message=f"{vuln_data.get('name')}: {vuln_data.get('vulns', [{}])[0].get('id', 'Unknown')}",
                            fix_suggestion=f"Upgrade to {vuln_data.get('fix_versions', ['latest'])[0]}",
                        )
                        vulnerabilities.append(vuln)
            except (asyncio.TimeoutError, FileNotFoundError, json.JSONDecodeError):
                pass

        return vulnerabilities


# Singleton instance
_security_service: Optional[SecurityService] = None


def get_security_service() -> SecurityService:
    """Get or create the security service singleton."""
    global _security_service
    if _security_service is None:
        _security_service = SecurityService()
    return _security_service
