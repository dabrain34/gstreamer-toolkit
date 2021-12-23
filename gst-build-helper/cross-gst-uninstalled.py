#!/usr/bin/env python3

import argparse
import json
import os
import platform
import re
import site
import shutil
import subprocess
import sys
import tempfile
import pathlib

from distutils.sysconfig import get_python_lib

#from common import get_meson

SCRIPTDIR = os.path.dirname(os.path.realpath(__file__))
PLATFORM_SPECIFIC_DIR = 'x86_64-linux-gnu'

# Use '_build' as the builddir instead of 'build'
DEFAULT_BUILDDIR = os.path.join(SCRIPTDIR, 'gst-build-install')
if not os.path.exists(DEFAULT_BUILDDIR):
    DEFAULT_BUILDDIR = os.path.join(SCRIPTDIR, '_build')


def listify(o):
    if isinstance(o, str):
        return [o]
    if isinstance(o, list):
        return o
    raise AssertionError('Object {!r} must be a string or a list'.format(o))

def stringify(o):
    if isinstance(o, str):
        return o
    if isinstance(o, list):
        if len(o) == 1:
            return o[0]
        raise AssertionError('Did not expect object {!r} to have more than one element'.format(o))
    raise AssertionError('Object {!r} must be a string or a list'.format(o))

def prepend_env_var(env, var, value):
    env[var] = os.pathsep + value + os.pathsep + env.get(var, "")
    env[var] = env[var].replace(os.pathsep + os.pathsep, os.pathsep).strip(os.pathsep)


def get_subprocess_env(options):
    env = os.environ.copy()
    PREFIX_DIR = os.path.join(options.builddir)

    env["CURRENT_GST"] = os.path.normpath(SCRIPTDIR)

    env["GST_VERSION"] = options.gst_version
    env["GST_ENV"] = 'gst-' + options.gst_version

    env["GST_REGISTRY"] = os.path.normpath(os.path.join(PREFIX_DIR, 'registry.dat'))
    env["GST_PLUGIN_SCANNER"] = os.path.join(PREFIX_DIR,'libexec',
                                             'gstreamer-1.0'
                                             , 'gst-plugin-scanner')

    #binaries
    prepend_env_var(env, "PATH", os.path.join(PREFIX_DIR, 'bin'))

    #libraries
    sharedlib_reg = re.compile(r'\.so|\.dylib|\.dll')
    typelib_reg = re.compile(r'.*\.typelib$')
    pluginpath_reg = re.compile(r'lib.*' + re.escape(os.path.normpath('/gstreamer-1.0/')))

    if os.name == 'nt':
        lib_path_envvar = 'PATH'
    elif platform.system() == 'Darwin':
        lib_path_envvar = 'DYLD_LIBRARY_PATH'
    else:
        lib_path_envvar = 'LD_LIBRARY_PATH'

    prepend_env_var(env, lib_path_envvar, os.path.join(PREFIX_DIR, 'lib'))
    prepend_env_var(env, lib_path_envvar, os.path.join(PREFIX_DIR, 'lib', options.platform))

    #plugins
    prepend_env_var(env, "GST_PLUGIN_PATH", os.path.join(PREFIX_DIR, 'lib', 'gstreamer-1.0'))
    prepend_env_var(env, "GST_PLUGIN_PATH", os.path.join(PREFIX_DIR, 'lib', options.platform, 'gstreamer-1.0'))

    # GStreamer validate tests.
    prepend_env_var(env, "GST_VALIDATE_SCENARIOS_PATH", os.path.join(
        PREFIX_DIR, 'share', 'gstreamer-1.0', 'validate', 'scenarios'))

    # GObject introspection
    prepend_env_var(env, "GI_TYPELIB_PATH", os.path.join(PREFIX_DIR, 'lib',
                                                         'lib', 'girepository-1.0'))
    # OMX Specific
    env["GST_OMX_CONFIG_DIR"] = os.path.join(PREFIX_DIR, 'etc', 'xdg')
    # Enable the logs
    env['GST_DEBUG'] = '*:2'

    return env

# https://stackoverflow.com/questions/1871549/determine-if-python-is-running-inside-virtualenv
def in_venv():
    return (hasattr(sys, 'real_prefix') or
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))

def python_env(options, unset_env=False):
    """
    Setup our overrides_hack.py as sitecustomize.py script in user
    site-packages if unset_env=False, else unset, previously set
    env.
    """
    subprojects_path = os.path.join(options.builddir, "subprojects")
    gst_python_path = os.path.join(SCRIPTDIR, "subprojects", "gst-python")
    if not os.path.exists(os.path.join(subprojects_path, "gst-python")) or \
            not os.path.exists(gst_python_path):
        return False

    if in_venv ():
        sitepackages = get_python_lib()
    else:
        sitepackages = site.getusersitepackages()

    if not sitepackages:
        return False

    sitecustomize = os.path.join(sitepackages, "sitecustomize.py")
    overrides_hack = os.path.join(gst_python_path, "testsuite", "overrides_hack.py")
    mesonconfig = os.path.join(gst_python_path, "testsuite", "mesonconfig.py")
    mesonconfig_link = os.path.join(sitepackages, "mesonconfig.py")

    if not unset_env:
        if os.path.exists(sitecustomize):
            if os.path.realpath(sitecustomize) == overrides_hack:
                print("Customize user site script already linked to the GStreamer one")
                return False

            old_sitecustomize = os.path.join(sitepackages,
                                            "old.sitecustomize.gstuninstalled.py")
            shutil.move(sitecustomize, old_sitecustomize)
        elif not os.path.exists(sitepackages):
            os.makedirs(sitepackages)

        os.symlink(overrides_hack, sitecustomize)
        os.symlink(mesonconfig, mesonconfig_link)
        return os.path.realpath(sitecustomize) == overrides_hack
    else:
        if not os.path.realpath(sitecustomize) == overrides_hack:
            return False

        os.remove(sitecustomize)
        os.remove (mesonconfig_link)
        old_sitecustomize = os.path.join(sitepackages,
                                            "old.sitecustomize.gstuninstalled.py")

        if os.path.exists(old_sitecustomize):
            shutil.move(old_sitecustomize, sitecustomize)

        return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="gstreamer-uninstalled")
    parser.add_argument('builddir', type=str,
                            default=SCRIPTDIR,
                            help='The install directory such as /usr/local' )
    parser.add_argument("--platform",
                        default=PLATFORM_SPECIFIC_DIR,
                        help="The target name folder such x86_64-linux-gnu")
    parser.add_argument("--gst-version", default="master",
                        help="The GStreamer major version")
    options, args = parser.parse_known_args()

    if not os.path.exists(options.builddir):
        print("GStreamer not built in %s\n\nBuild it and try again" %
              options.builddir)
        exit(1)

    if not args:
        if os.name == 'nt':
            args = [os.environ.get("COMSPEC", r"C:\WINDOWS\system32\cmd.exe")]
        else:
            args = [os.environ.get("SHELL", os.path.realpath("/bin/sh"))]
        if "bash" in args[0]:
            bashrc = os.path.expanduser('~/.bashrc')
            if os.path.exists(bashrc):
                tmprc = tempfile.NamedTemporaryFile(mode='w')
                with open(bashrc, 'r') as src:
                    shutil.copyfileobj(src, tmprc)
                tmprc.write('\nexport PS1="[gst-%s] $PS1"' % options.gst_version)
                tmprc.flush()
                # Let the GC remove the tmp file
                args.append("--rcfile")
                args.append(tmprc.name)
    python_set = python_env(options)
    try:
        exit(subprocess.call(args, cwd=options.builddir, close_fds=False,
                             env=get_subprocess_env(options)))
    except subprocess.CalledProcessError as e:
        exit(e.returncode)
    finally:
        if python_set:
            python_env(options, unset_env=True)
