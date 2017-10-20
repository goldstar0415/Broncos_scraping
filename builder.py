import glob
from subprocess import call

class EggBuildError(Exception):
    pass

def build():
    ret = call(("python3", "setup.py", "build"))
    ret = call(("python3", "setup.py", "sdist"))
    ret = call(("python3", "setup.py", "bdist_egg"))

    eggs = glob.glob('*/*.egg', recursive=True)

    if len(eggs) == 1:
        return eggs[0]
    else:
        raise EggBuildError("Multiple eggs found")
