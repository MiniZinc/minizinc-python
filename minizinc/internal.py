import re
import shutil
import subprocess

# Oldest MiniZinc version known to work with these definitions
REQUIRED_MINIZINC = (2, 2, 0)

# Try to locate the MiniZinc executable
__exec = shutil.which("minizinc")

if __exec is None:
    raise ImportWarning("MiniZinc not found")
else:
    # Define internal functions using MiniZinc executable
    def _version():
        output = subprocess.run([__exec, "--version"], capture_output=True, check=True)
        match = re.search(r'version (\d+)\.(\d+)\.(\d+)', output.stdout.decode())
        return tuple([int(i) for i in match.groups()])

# Check compatibility of the MiniZinc version
__version = _version()
if __version < REQUIRED_MINIZINC:
    raise ImportWarning("Unsupported MiniZinc version, minimal required version %d.%d.%d (found %d.%d.%d)"
                        % (REQUIRED_MINIZINC + __version))
