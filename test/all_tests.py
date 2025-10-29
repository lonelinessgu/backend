import subprocess
import sys
import os


def run_tests():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)

    result = subprocess.run([
        sys.executable, "-m", "pytest",
        "test",
        "-v",
        "--tb=long"
    ])
    return result.returncode


if __name__ == "__main__":
    exit(run_tests())