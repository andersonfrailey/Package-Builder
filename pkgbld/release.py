"""
Policy Simulaton Library (PSL) model Anaconda-Cloud package release logic.
"""
# CODING-STYLE CHECKS:
# pycodestyle release.py
# pylint --disable=locally-disabled release.py

import os
import re
import shutil
import pkgbld.utils as u


PYTHON_VERSIONS = ['3.6']
OS_PLATFORMS = ['osx-64', 'linux-64', 'win-32', 'win-64']

GITHUB_URL = 'https://github.com/open-source-economics'
ANACONDA_USER = 'pslmodels'
ANACONDA_CHANNEL = ANACONDA_USER
HOME_DIR = os.path.expanduser('~')
ANACONDA_TOKEN_FILE = os.path.join(
    HOME_DIR,
    '.{}_anaconda_token'.format(ANACONDA_USER)
)
WORKING_DIR = os.path.join(
    HOME_DIR,
    'temporary_pkgbld_working_dir'
)
BUILDS_DIR = 'pkgbuilds'


def release(repo_name, pkg_name, version):
    """
    Conduct local build and upload to Anaconda Cloud of conda packages
    for each platform for specified Policy Simulation Library (PSL) model
    and version.

    Parameters
    ----------
    repo_name: string
        model repository name appended to GITHUB_URL

    pkg_name: string
        model package name for repository specified by repo_name

    version: string
        model version string consistent with semantic versioning;
        must be a release tag in the model repository

    Raises
    ------
    ValueError:
        if parameters are not valid
        if ANACONDA_TOKEN_FILE does not exist

    Returns
    -------
    Nothing

    Notes
    -----
    Example usage: release('Tax-Calculator', 'taxcalc', '0.23.0')
    """
    # check parameters
    if not isinstance(repo_name, str):
        raise ValueError('repo_name is not a string object')
    if not isinstance(pkg_name, str):
        raise ValueError('pkg_name is not a string object')
    if not isinstance(version, str):
        raise ValueError('version is not a string object')
    pattern = r'^[0-9]+\.[0-9]+\.[0-9]+$'
    if re.match(pattern, version) is None:
        msg = 'version=<{}> does not follow semantic-versioning rules'
        raise ValueError(msg.format(version))

    # get token
    if not os.path.isfile(ANACONDA_TOKEN_FILE):
        msg = 'Anaconda token file {} does not exist'
        raise ValueError(msg.format(ANACONDA_TOKEN_FILE))
    with open(ANACONDA_TOKEN_FILE, 'r') as tfile:
        token = tfile.read()

    # make empty working directory
    if os.path.isdir(WORKING_DIR):
        shutil.rmtree(WORKING_DIR)
    os.mkdir(WORKING_DIR)
    os.chdir(WORKING_DIR)

    print('Package-Builder release:')
    print('repo_name = {}'.format(repo_name))
    print('pkg_name = {}'.format(pkg_name))
    print('version = {}'.format(version))
    print('token = {}'.format(token))

    # clone model repository and checkout model version
    cmd = 'git clone {}/{}/'.format(GITHUB_URL, repo_name)
    u.os_call(cmd)
    os.chdir(repo_name)
    cmd = 'git checkout -b v{ver} {ver}'.format(ver=version)
    u.os_call(cmd)

    # specify version in repository's conda.recipe/meta.yaml file
    u.specify_version(version)

    # build and upload model package for each Python version and OS platform
    local_platform = u.conda_platform_name()
    for pyver in PYTHON_VERSIONS:
        # ... build for local_platform
        cmd = ('conda build --python {} --old-build-string '
               '--channel {} --override-channels '
               '--no-anaconda-upload --output-folder {} '
               'conda.recipe').format(pyver, ANACONDA_CHANNEL, BUILDS_DIR)
        u.os_call(cmd)
        # ... convert local build to other OS_PLATFORMS
        pyver_parts = pyver.split('.')
        pystr = pyver_parts[0] + pyver_parts[1]
        pkgfile = os.path.join(BUILDS_DIR,
                               '{}'.format(local_platform),
                               '{}-{}-py{}_0.tar.bz2'.format(pkg_name,
                                                             version, pystr))
        for platform in OS_PLATFORMS:
            if platform == local_platform:
                continue
            cmd = 'conda convert -p {} -o {} {}'.format(platform,
                                                        BUILDS_DIR, pkgfile)
            u.os_call(cmd)
        # ... upload to Anaconda Cloud

    # remove working directory and its contents
    os.chdir(HOME_DIR)
    shutil.rmtree(WORKING_DIR)
