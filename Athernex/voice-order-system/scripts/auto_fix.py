"""
Auto-fix script for common issues in Voice Order System.

Fixes:
1. Missing Python packages
2. Config module import issues
3. Missing __init__.py files
4. fastText model download
5. Piper TTS dependency issues

Usage:
    python scripts/auto_fix.py
    python scripts/auto_fix.py --skip-packages  # Skip package installation
    python scripts/auto_fix.py --skip-model     # Skip model download
"""

import sys
import subprocess
import os
from pathlib import Path
import argparse


class AutoFixer:
    """Automatic fixer for common issues."""
    
    def __init__(self, skip_packages=False, skip_model=False):
        self.skip_packages = skip_packages
        self.skip_model = skip_model
        self.project_root = Path(__file__).parent.parent
        self.fixes_applied = []
        self.fixes_failed = []
    
    def print_header(self, title):
        """Print section header."""
        print(f"\n{'='*80}")
        print(f"  {title}")
        print(f"{'='*80}\n")
    
    def run_command(self, cmd, description):
        """Run a shell command and report result."""
        print(f"Running: {description}")
        print(f"Command: {' '.join(cmd)}")
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            print(f"✓ Success: {description}")
            self.fixes_applied.append(description)
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed: {description}")
            print(f"  Error: {e.stderr[:200]}")
            self.fixes_failed.append(description)
            return False
    
    # Fix 1: Install missing packages
    def fix_missing_packages(self):
        """Install missing Python packages."""
        self.print_header("FIX 1: Installing Missing Packages")
        
        if self.skip_packages:
            print("Skipped (--skip-packages flag)")
            return
        
        # Check which packages are missing
        packages_to_check = [
            "fasttext",
            "edge-tts",
            "ollama",
            "piper-tts",
        ]
        
        missing = []
        for package in packages_to_check:
            try:
                __import__(package.replace("-", "_"))
                print(f"✓ {package} already installed")
            except ImportError:
                missing.append(package)
                print(f"✗ {package} missing")
        
        if missing:
            print(f"\nInstalling {len(missing)} missing packages...")
            for package in missing:
                self.run_command(
                    [sys.executable, "-m", "pip", "install", package],
                    f"Install {package}"
                )
        else:
            print("\n✓ All packages already installed")
    
    # Fix 2: Fix config module import
    def fix_config_import(self):
        """Fix config module import issues."""
        self.print_header("FIX 2: Fixing Config Module Import")
        
        # Check if config/__init__.py exists
        config_init = self.project_root / "config" / "__init__.py"
        
        if not config_init.exists():
            print(f"Creating {config_init}")
            config_init.write_text('"""Configuration package."""\n\nfrom .config import settings\n\n__all__ = ["settings"]\n')
            print(f"✓ Created config/__init__.py")
            self.fixes_applied.append("Created config/__init__.py")
        else:
            print(f"✓ config/__init__.py already exists")
        
        # Verify it works
        sys.path.insert(0, str(self.project_root))
        try:
            from config import settings
            print(f"✓ Config module imports successfully")
        except Exception as e:
            print(f"✗ Config module still has issues: {e}")
            self.fixes_failed.append("Config module import")
    
    # Fix 3: Fix TTS base import (piper dependency)
    def fix_tts_base(self):
        """Fix TTS base module import issues."""
        self.print_header("FIX 3: Fixing TTS Base Module")
        
        tts_base_file = self.project_root / "src" / "tts" / "base.py"
        
        if not tts_base_file.exists():
            print(f"✗ {tts_base_file} not found")
            self.fixes_failed.append("TTS base file missing")
            return
        
        # Read the file
        content = tts_base_file.read_text()
        
        # Check if it has piper import issues
        if "import piper" in content.lower() or "from piper" in content.lower():
            print("⚠ TTS base has piper imports (may cause issues)")
            print("  Piper is optional - the module should handle ImportError")
        else:
            print("✓ TTS base looks OK (no direct piper imports)")
        
        # Try importing
        sys.path.insert(0, str(self.project_root / "src"))
        try:
            from tts.base import TTSEngine
            print("✓ TTS base imports successfully")
        except Exception as e:
            print(f"✗ TTS base import error: {e}")
            self.fixes_failed.append("TTS base import")
    
    # Fix 4: Create missing __init__.py files
    def fix_missing_init_files(self):
        """Create missing __init__.py files."""
        self.print_header("FIX 4: Creating Missing __init__.py Files")
        
        # Directories that should have __init__.py
        dirs_needing_init = [
            "src",
            "src/stt",
            "src/llm",
            "src/tts",
            "src/language",
            "src/dialogue",
            "src/orchestration",
            "src/api",
            "src/audio",
            "src/confidence",
            "src/utils",
            "config",
            "tests",
        ]
        
        created = 0
        for dir_path in dirs_needing_init:
            full_dir = self.project_root / dir_path
            init_file = full_dir / "__init__.py"
            
            if full_dir.exists() and not init_file.exists():
                # Create minimal __init__.py
                module_name = dir_path.split("/")[-1].title()
                init_file.write_text(f'"""{module_name} module."""\n')
                print(f"✓ Created {init_file}")
                created += 1
            elif init_file.exists():
                print(f"✓ {dir_path}/__init__.py exists")
        
        if created > 0:
            self.fixes_applied.append(f"Created {created} __init__.py files")
        else:
            print("\n✓ All __init__.py files already exist")
    
    # Fix 5: Download fastText model
    def fix_fasttext_model(self):
        """Download fastText model if missing."""
        self.print_header("FIX 5: Downloading fastText Model")
        
        if self.skip_model:
            print("Skipped (--skip-model flag)")
            return
        
        model_path = Path.home() / ".fasttext" / "lid.176.bin"
        
        if model_path.exists():
            size_mb = model_path.stat().st_size / (1024 * 1024)
            print(f"✓ Model already exists ({size_mb:.1f} MB)")
            return
        
        print(f"Model not found at {model_path}")
        print("Downloading fastText model (131 MB)...")
        
        # Run setup script
        setup_script = self.project_root / "scripts" / "setup_fasttext.py"
        if setup_script.exists():
            self.run_command(
                [sys.executable, str(setup_script)],
                "Download fastText model"
            )
        else:
            print(f"✗ Setup script not found: {setup_script}")
            print("  Manual download:")
            print(f"    mkdir {model_path.parent}")
            print(f"    wget -O {model_path} https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin")
            self.fixes_failed.append("fastText model download")
    
    # Fix 6: Fix pydantic compatibility
    def fix_pydantic_compatibility(self):
        """Fix pydantic v2 compatibility issues."""
        self.print_header("FIX 6: Checking Pydantic Compatibility")
        
        try:
            import pydantic
            version = pydantic.__version__
            major_version = int(version.split('.')[0])
            
            print(f"Pydantic version: {version}")
            
            if major_version >= 2:
                print("✓ Pydantic v2 detected")
                
                # Check if pydantic-settings is installed
                try:
                    import pydantic_settings
                    print("✓ pydantic-settings installed")
                except ImportError:
                    print("✗ pydantic-settings not installed")
                    self.run_command(
                        [sys.executable, "-m", "pip", "install", "pydantic-settings"],
                        "Install pydantic-settings"
                    )
            else:
                print(f"⚠ Pydantic v1 detected (v2 recommended)")
                
        except ImportError:
            print("✗ Pydantic not installed")
            self.fixes_failed.append("Pydantic check")
    
    # Fix 7: Verify all imports work
    def verify_imports(self):
        """Verify all critical imports work."""
        self.print_header("FIX 7: Verifying Module Imports")
        
        sys.path.insert(0, str(self.project_root / "src"))
        
        modules_to_test = [
            ("config.config", "Config"),
            ("stt.base", "STT Base"),
            ("llm.base", "LLM Base"),
            ("tts.base", "TTS Base"),
            ("language.detector", "Language Detector"),
            ("language.fasttext_detector", "fastText Detector"),
            ("language.hybrid_detector", "Hybrid Detector"),
            ("dialogue.manager", "Dialogue Manager"),
            ("orchestration.orchestrator", "Orchestrator"),
            ("orchestration.pipeline", "Pipeline"),
            ("orchestration.order_manager", "Order Manager"),
            ("orchestration.cache", "Cache Manager"),
            ("api.main", "API Main"),
        ]
        
        passed = 0
        failed = 0
        
        for module_path, name in modules_to_test:
            try:
                __import__(module_path)
                print(f"✓ {name:30} OK")
                passed += 1
            except Exception as e:
                print(f"✗ {name:30} ERROR: {str(e)[:50]}")
                failed += 1
        
        print(f"\nImport Results: {passed} passed, {failed} failed")
        
        if failed > 0:
            self.fixes_failed.append(f"{failed} module imports failed")
    
    # Main runner
    def run_all_fixes(self):
        """Run all fixes."""
        self.print_header("VOICE ORDER SYSTEM - AUTO FIX")
        
        print("This script will automatically fix common issues.")
        print("Press Ctrl+C to cancel at any time.\n")
        
        try:
            self.fix_missing_packages()
            self.fix_config_import()
            self.fix_missing_init_files()
            self.fix_pydantic_compatibility()
            self.fix_tts_base()
            self.fix_fasttext_model()
            self.verify_imports()
            
            self.print_summary()
            
        except KeyboardInterrupt:
            print("\n\n✗ Cancelled by user")
            sys.exit(1)
    
    def print_summary(self):
        """Print summary of fixes."""
        self.print_header("AUTO-FIX SUMMARY")
        
        print(f"Fixes Applied: {len(self.fixes_applied)}")
        for fix in self.fixes_applied:
            print(f"  ✓ {fix}")
        
        if self.fixes_failed:
            print(f"\nFixes Failed: {len(self.fixes_failed)}")
            for fix in self.fixes_failed:
                print(f"  ✗ {fix}")
        
        print()
        if not self.fixes_failed:
            print("✓ ALL FIXES APPLIED SUCCESSFULLY!")
            print("\nNext steps:")
            print("1. Run: python scripts/quick_diagnostic.py")
            print("2. Start Ollama: ollama serve")
            print("3. Test the system: python scripts/test_fasttext_quick.py")
        else:
            print("⚠ SOME FIXES FAILED")
            print("\nPlease review the errors above and fix manually.")
        
        print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Auto-fix common issues")
    parser.add_argument("--skip-packages", action="store_true", help="Skip package installation")
    parser.add_argument("--skip-model", action="store_true", help="Skip model download")
    
    args = parser.parse_args()
    
    fixer = AutoFixer(
        skip_packages=args.skip_packages,
        skip_model=args.skip_model
    )
    fixer.run_all_fixes()


if __name__ == "__main__":
    main()
