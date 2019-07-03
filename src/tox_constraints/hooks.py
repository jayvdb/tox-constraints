"""Simple tox plugin to facilitate working with abstract and concrete dependencies"""
from collections import defaultdict
from pathlib import Path

import tox  # type: ignore

REQ_PATH = Path("requirements")

HEADER = """\
#
# This file is autogenerated by tox-constraints
# It is updated every time tox runs
#
"""


def _patch_envconfigs(envconfigs):
    for name, envconfig in envconfigs.items():
        if name == ".package":
            # Don't patch isolated packaging environment because some parsing will fail
            # on -cconstraints.txt
            continue
        if envconfig.skip_install is True and not envconfig.deps:
            # Avoid attempting to install no packages as pip does not like this:
            # > ERROR: You must give at least one requirement to install
            continue

        for dep in envconfig.deps:
            if dep.name.startswith("-c"):
                break
        else:
            envconfig.deps.append(tox.config.DepConfig("-cconstraints.txt"))

        if envconfig.skip_install is True:
            pass
        elif envconfig.skip_install is False:
            envconfig.deps.append(
                tox.config.DepConfig("-r" + str(REQ_PATH / "install_requires.txt"))
            )
        else:
            raise ValueError


def _save_if_different(path: Path, new_content: str):
    """Save `new_content` to file if it is different to the existing content.

    Useful e.g. for only touching files when they change to avoid triggering make.
    """
    try:
        with path.open("r") as fp:
            old_content = fp.read()
    except FileNotFoundError:
        old_content = None

    if old_content != new_content:
        with path.open("w") as fp:
            fp.write(new_content)


def _export_deps(envconfigs):
    if not REQ_PATH.exists():
        REQ_PATH.mkdir()

    dep2names = defaultdict(list)
    for name, envconfig in envconfigs.items():
        for dep in envconfig.deps:
            if dep.name.startswith("-r"):
                continue  # Potential loop

            if dep.name.startswith("-c"):
                continue  # Constraint override

            dep2names[str(dep)].append(name)

    dep_len = max(len(dep) for dep in dep2names)
    lines = [
        f"{dep:<{dep_len}}  # from {', '.join(sorted(dep2names[dep]))}\n"
        for dep in sorted(dep2names)
    ]
    _save_if_different(REQ_PATH / "tox.txt", HEADER + "".join(lines))


@tox.hookimpl
def tox_configure(config):
    """Apply concrete constraints and export abstract dependencies"""
    _export_deps(config.envconfigs)
    _patch_envconfigs(config.envconfigs)
