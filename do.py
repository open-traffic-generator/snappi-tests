import fnmatch
import os
import re
import sys
import shutil
import subprocess


def setup():
    run(
        [
            py() + " -m pip install --upgrade pip",
            py() + " -m pip install --upgrade virtualenv",
            py() + " -m virtualenv .env",
        ]
    )


def init():
    run(
        [
            py() + " -m pip install -r requirements.txt",
        ]
    )


def get_version():
    if os.path.exists("version.txt"):
        with open("version.txt") as f:
            out = f.read()
            workflow_id = re.findall(r"workflow_id: (.+)", out)
            if workflow_id:
                workflow_id = workflow_id[0]
            version_info = re.findall(r"version: (.+)", out)
            if version_info:
                version_info = version_info[0]
                snappi_convergence = re.findall(
                    r"snappi_convergence: (.+)", out
                )[0]

        if version_info:
            new_data = []
            with open("requirements.txt") as f:
                out = f.readlines()
                for line in out:
                    match = re.search(
                        r"snappi\[convergence,ixnetwork\]==.*", line
                    )
                    if match:
                        snappi_convergence = (
                            "snappi_convergence==" + snappi_convergence + "\n"
                        )
                        new_data.append("snappi" + "\n")
                        new_data.append(snappi_convergence)
                        new_version = (
                            "snappi-ixnetwork==" + version_info + "\n"
                        )
                        new_data.append(new_version)
                    else:
                        new_data.append(line)
            f.close()
            with open("requirements.txt", "w+") as f:
                f.writelines(new_data)
        elif workflow_id:
            print(workflow_id)


def clear_version_file():
    with open("version.txt", "w+") as f:
        f.close()


def lint():
    paths = ["tests", "do.py"]

    run(
        [
            py() + " -m black " + " ".join(paths),
            py() + " -m flake8 " + " ".join(paths),
        ]
    )


def test():
    args = [
        '--location="https://otg-novus100g.lbj.is.keysight.com:5000"',
        (
            '--ports="otg-novus100g.lbj.is.keysight.com;1;1'
            " otg-novus100g.lbj.is.keysight.com;1;2"
            " otg-novus100g.lbj.is.keysight.com;1;3"
            ' otg-novus100g.lbj.is.keysight.com;1;4"'
        ),
        "--ext=ixnetwork",
        "--speed=speed_100_gbps",
        "tests",
        '-m "not dut and not l1_manual"',
    ]
    run(
        [
            py() + " -m pytest -svvv {}".format(" ".join(args)),
        ]
    )


def uhd_test():
    args = [
        '--location="https://10.36.70.75"',
        (
            '--ports="localuhd/25 localuhd/26 localuhd/27 localuhd/28"'
        ),
        "--ext=ixnetwork",
        "--speed=speed_100_gbps",
        "--uhd=true",
        "tests",
        '-m "not dut and not l1_manual and not non_uhd"'
    ]
    run(
        [
            py() + " -m pytest -svvv {}".format(" ".join(args)),
        ]
    )


def dist():
    clean()
    run(
        [
            py() + " setup.py sdist bdist_wheel --universal",
        ]
    )
    print(os.listdir("dist"))


def install():
    wheel = "{}-{}-py2.py3-none-any.whl".format(*pkg())
    run(
        [
            "{} -m pip install --upgrade --force-reinstall {}[testing]".format(
                py(), os.path.join("dist", wheel)
            ),
        ]
    )


def release():
    run(
        [
            py() + " -m pip install --upgrade twine",
            "{} -m twine upload -u {} -p {} dist/*".format(
                py(),
                os.environ["PYPI_USERNAME"],
                os.environ["PYPI_PASSWORD"],
            ),
        ]
    )


def clean():
    """
    Removes filenames or dirnames matching provided patterns.
    """
    pwd_patterns = [
        ".pytype",
        "dist",
        "build",
        "*.egg-info",
    ]
    recursive_patterns = [
        ".pytest_cache",
        "__pycache__",
        "*.pyc",
        "*.log",
    ]

    for pattern in pwd_patterns:
        for path in pattern_find(".", pattern, recursive=False):
            rm_path(path)

    for pattern in recursive_patterns:
        for path in pattern_find(".", pattern, recursive=True):
            rm_path(path)


def version():
    print(pkg()[-1])


def pkg():
    """
    Returns name of python package in current directory and its version.
    """
    try:
        return pkg.pkg
    except AttributeError:
        with open("setup.py") as f:
            out = f.read()
            name = re.findall(r"pkg_name = \"(.+)\"", out)[0]
            version = re.findall(r"version = \"(.+)\"", out)[0]

            pkg.pkg = (name, version)
        return pkg.pkg


def rm_path(path):
    """
    Removes a path if it exists.
    """
    if os.path.exists(path):
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)


def pattern_find(src, pattern, recursive=True):
    """
    Recursively searches for a dirname or filename matching given pattern and
    returns all the matches.
    """
    matches = []

    if not recursive:
        for name in os.listdir(src):
            if fnmatch.fnmatch(name, pattern):
                matches.append(os.path.join(src, name))
        return matches

    for dirpath, dirnames, filenames in os.walk(src):
        for names in [dirnames, filenames]:
            for name in names:
                if fnmatch.fnmatch(name, pattern):
                    matches.append(os.path.join(dirpath, name))

    return matches


def py():
    """
    Returns path to python executable to be used.
    """
    try:
        return py.path
    except AttributeError:
        py.path = os.path.join(".env", "bin", "python")
        if not os.path.exists(py.path):
            py.path = sys.executable

        # since some paths may contain spaces
        py.path = '"' + py.path + '"'
        return py.path


def run(commands):
    """
    Executes a list of commands in a native shell and raises exception upon
    failure.
    """
    try:
        for cmd in commands:
            print(cmd)
            subprocess.check_call(
                cmd.encode("utf-8", errors="ignore"), shell=True
            )
    except Exception:
        sys.exit(1)


def main():
    if len(sys.argv) >= 2:
        globals()[sys.argv[1]](*sys.argv[2:])
    else:
        print("usage: python do.py [args]")


if __name__ == "__main__":
    main()
