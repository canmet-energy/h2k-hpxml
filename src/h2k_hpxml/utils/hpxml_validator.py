"""
HPXML Validator

Validates HPXML files against the H2K-HPXML subset schema.
Provides detailed error messages and supports batch validation.

Usage:
    # As a module
    from h2k_hpxml.utils.hpxml_validator import validate_hpxml, batch_validate

    result = validate_hpxml("output.xml")
    if result.is_valid:
        print("Valid HPXML!")
    else:
        for error in result.errors:
            print(f"Line {error.line}: {error.message}")

    # Command-line
    python -m h2k_hpxml.utils.hpxml_validator output.xml
    python -m h2k_hpxml.utils.hpxml_validator --batch output_folder/
"""

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Tuple

try:
    from lxml import etree
    HAS_LXML = True
except ImportError:
    HAS_LXML = False


@dataclass
class ValidationError:
    """Represents a single validation error"""
    line: int
    column: int
    message: str
    error_type: str
    element: Optional[str] = None

    def __str__(self) -> str:
        if self.element:
            return f"Line {self.line}, Column {self.column} [{self.error_type}]: {self.message} (Element: {self.element})"
        return f"Line {self.line}, Column {self.column} [{self.error_type}]: {self.message}"


@dataclass
class ValidationResult:
    """Result of HPXML validation"""
    file_path: Path
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        if self.is_valid:
            return f"✓ {self.file_path}: Valid"
        else:
            error_count = len(self.errors)
            return f"✗ {self.file_path}: {error_count} error(s)"

    def format_errors(self, max_errors: int = 10) -> str:
        """Format errors for display"""
        if self.is_valid:
            return "No errors found."

        lines = [f"\nValidation errors in {self.file_path}:"]
        displayed_errors = self.errors[:max_errors]

        for i, error in enumerate(displayed_errors, 1):
            lines.append(f"  {i}. {error}")

        if len(self.errors) > max_errors:
            lines.append(f"  ... and {len(self.errors) - max_errors} more error(s)")

        return "\n".join(lines)


class HPXMLValidator:
    """Validator for HPXML files using the H2K-HPXML subset schema"""

    def __init__(self, schema_path: Optional[Path] = None):
        """
        Initialize the validator

        Args:
            schema_path: Path to the HPXML subset XSD file.
                        If None, uses the default schema location.
        """
        if not HAS_LXML:
            raise ImportError(
                "lxml is required for HPXML validation. "
                "Install it with: pip install lxml"
            )

        if schema_path is None:
            # Default schema location
            module_dir = Path(__file__).parent.parent
            schema_path = module_dir / "resources" / "schemas" / "hpxml_subset.xsd"

        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")

        self.schema_path = schema_path
        self._schema = None
        self._load_schema()

    def _load_schema(self):
        """Load and parse the XSD schema"""
        try:
            with open(self.schema_path, 'rb') as f:
                schema_doc = etree.parse(f)
            self._schema = etree.XMLSchema(schema_doc)
        except etree.XMLSchemaParseError as e:
            raise ValueError(f"Failed to parse schema: {e}")

    def validate(self, hpxml_file: Path, verbose: bool = False) -> ValidationResult:
        """
        Validate an HPXML file against the subset schema

        Args:
            hpxml_file: Path to the HPXML file to validate
            verbose: If True, include additional warnings

        Returns:
            ValidationResult with validation status and errors
        """
        hpxml_file = Path(hpxml_file)

        if not hpxml_file.exists():
            return ValidationResult(
                file_path=hpxml_file,
                is_valid=False,
                errors=[ValidationError(
                    line=0,
                    column=0,
                    message=f"File not found: {hpxml_file}",
                    error_type="FileNotFound"
                )]
            )

        try:
            # Parse the HPXML file
            with open(hpxml_file, 'rb') as f:
                doc = etree.parse(f)

            # Validate against schema
            is_valid = self._schema.validate(doc)

            errors = []
            if not is_valid:
                errors = self._parse_errors(self._schema.error_log)

            warnings = []
            if verbose:
                warnings = self._check_warnings(doc)

            return ValidationResult(
                file_path=hpxml_file,
                is_valid=is_valid,
                errors=errors,
                warnings=warnings
            )

        except etree.XMLSyntaxError as e:
            return ValidationResult(
                file_path=hpxml_file,
                is_valid=False,
                errors=[ValidationError(
                    line=e.lineno or 0,
                    column=e.position[1] if e.position else 0,
                    message=str(e),
                    error_type="XMLSyntaxError"
                )]
            )
        except Exception as e:
            return ValidationResult(
                file_path=hpxml_file,
                is_valid=False,
                errors=[ValidationError(
                    line=0,
                    column=0,
                    message=f"Unexpected error: {e}",
                    error_type="UnexpectedError"
                )]
            )

    def _parse_errors(self, error_log) -> List[ValidationError]:
        """Parse lxml error log into ValidationError objects"""
        errors = []
        for error in error_log:
            # Extract element name from error path if available
            element = None
            if hasattr(error, 'path'):
                parts = error.path.split('/')
                if parts:
                    element = parts[-1]

            # Categorize error type
            error_type = "ValidationError"
            message = error.message

            if "not expected" in message.lower():
                error_type = "UnexpectedElement"
            elif "missing" in message.lower() or "required" in message.lower():
                error_type = "MissingElement"
            elif "invalid" in message.lower():
                error_type = "InvalidValue"
            elif "type" in message.lower():
                error_type = "TypeError"

            errors.append(ValidationError(
                line=error.line,
                column=error.column,
                message=message,
                error_type=error_type,
                element=element
            ))

        return errors

    def _check_warnings(self, doc) -> List[str]:
        """Check for potential issues that aren't schema violations"""
        warnings = []

        # Check schema version
        root = doc.getroot()
        schema_version = root.get('schemaVersion')
        if schema_version != '4.0':
            warnings.append(f"Schema version is '{schema_version}', expected '4.0'")

        # Check for empty elements
        for elem in root.iter():
            if elem.text is None and len(elem) == 0 and len(elem.attrib) == 0:
                warnings.append(f"Empty element found: {elem.tag}")

        return warnings

    def batch_validate(
        self,
        directory: Path,
        pattern: str = "*.xml",
        recursive: bool = True,
        verbose: bool = False
    ) -> Tuple[List[ValidationResult], Dict[str, int]]:
        """
        Validate multiple HPXML files in a directory

        Args:
            directory: Directory containing HPXML files
            pattern: Glob pattern for matching files (default: "*.xml")
            recursive: If True, search subdirectories
            verbose: If True, include warnings

        Returns:
            Tuple of (results list, summary dict)
        """
        directory = Path(directory)
        if not directory.is_dir():
            raise ValueError(f"Not a directory: {directory}")

        # Find files
        if recursive:
            files = list(directory.rglob(pattern))
        else:
            files = list(directory.glob(pattern))

        if not files:
            print(f"No files matching '{pattern}' found in {directory}")
            return [], {
                'total': 0,
                'valid': 0,
                'invalid': 0,
                'total_errors': 0
            }

        # Validate each file
        results = []
        for file_path in files:
            result = self.validate(file_path, verbose=verbose)
            results.append(result)

        # Generate summary
        summary = {
            'total': len(results),
            'valid': sum(1 for r in results if r.is_valid),
            'invalid': sum(1 for r in results if not r.is_valid),
            'total_errors': sum(len(r.errors) for r in results)
        }

        return results, summary


# Convenience functions for module-level usage

_validator_instance = None


def get_validator(schema_path: Optional[Path] = None) -> HPXMLValidator:
    """Get a singleton validator instance"""
    global _validator_instance
    if _validator_instance is None or schema_path is not None:
        _validator_instance = HPXMLValidator(schema_path)
    return _validator_instance


def validate_hpxml(
    hpxml_file: Path,
    schema_path: Optional[Path] = None,
    verbose: bool = False
) -> ValidationResult:
    """
    Validate an HPXML file (convenience function)

    Args:
        hpxml_file: Path to HPXML file
        schema_path: Optional custom schema path
        verbose: Include warnings

    Returns:
        ValidationResult
    """
    validator = get_validator(schema_path)
    return validator.validate(hpxml_file, verbose=verbose)


def batch_validate(
    directory: Path,
    pattern: str = "*.xml",
    recursive: bool = True,
    schema_path: Optional[Path] = None,
    verbose: bool = False
) -> Tuple[List[ValidationResult], Dict[str, int]]:
    """
    Batch validate HPXML files (convenience function)

    Args:
        directory: Directory containing files
        pattern: Glob pattern
        recursive: Search subdirectories
        schema_path: Optional custom schema path
        verbose: Include warnings

    Returns:
        Tuple of (results, summary)
    """
    validator = get_validator(schema_path)
    return validator.batch_validate(directory, pattern, recursive, verbose)


# CLI Interface

def main():
    """Command-line interface for HPXML validation"""
    parser = argparse.ArgumentParser(
        description="Validate HPXML files against H2K-HPXML subset schema",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate a single file
  python -m h2k_hpxml.utils.hpxml_validator output.xml

  # Batch validate a directory
  python -m h2k_hpxml.utils.hpxml_validator --batch output_folder/

  # Recursive validation with custom schema
  python -m h2k_hpxml.utils.hpxml_validator --batch output/ --recursive --schema custom.xsd

  # Verbose mode with warnings
  python -m h2k_hpxml.utils.hpxml_validator output.xml --verbose
        """
    )

    parser.add_argument(
        'path',
        type=Path,
        help='HPXML file or directory to validate'
    )

    parser.add_argument(
        '--batch',
        action='store_true',
        help='Batch validate all XML files in directory'
    )

    parser.add_argument(
        '--pattern',
        default='*.xml',
        help='Glob pattern for batch validation (default: *.xml)'
    )

    parser.add_argument(
        '--recursive',
        action='store_true',
        default=False,
        help='Search subdirectories in batch mode'
    )

    parser.add_argument(
        '--schema',
        type=Path,
        help='Path to custom XSD schema file'
    )

    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Show warnings and additional details'
    )

    parser.add_argument(
        '--max-errors',
        type=int,
        default=10,
        help='Maximum number of errors to display per file (default: 10)'
    )

    parser.add_argument(
        '--quiet',
        '-q',
        action='store_true',
        help='Only show summary, not individual results'
    )

    args = parser.parse_args()

    try:
        if args.batch:
            # Batch validation
            results, summary = batch_validate(
                directory=args.path,
                pattern=args.pattern,
                recursive=args.recursive,
                schema_path=args.schema,
                verbose=args.verbose
            )

            # Display results
            if not args.quiet:
                for result in results:
                    print(result)
                    if not result.is_valid and args.verbose:
                        print(result.format_errors(args.max_errors))

            # Display summary
            print(f"\n{'=' * 60}")
            print(f"Validation Summary:")
            print(f"  Total files: {summary['total']}")
            print(f"  Valid: {summary['valid']}")
            print(f"  Invalid: {summary['invalid']}")
            print(f"  Total errors: {summary['total_errors']}")

            # Exit code based on results
            sys.exit(0 if summary['invalid'] == 0 else 1)

        else:
            # Single file validation
            result = validate_hpxml(
                hpxml_file=args.path,
                schema_path=args.schema,
                verbose=args.verbose
            )

            print(result)

            if not result.is_valid:
                print(result.format_errors(args.max_errors))
                sys.exit(1)
            else:
                if args.verbose and result.warnings:
                    print("\nWarnings:")
                    for warning in result.warnings:
                        print(f"  - {warning}")
                sys.exit(0)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == '__main__':
    main()
