#!/usr/bin/env python3

import argparse
import contextlib
import json
import os
import platform
import shlex
import subprocess
import shutil

MESON_CROSS_FILE_TPL = \
    '''
[host_machine]
system = '{system}'
cpu_family = '{cpu_family}'
cpu = '{cpu}'
endian = '{endian}'

[properties]
{extra_properties}

[binaries]
c = {CC}
cpp = {CXX}
ar = {AR}
pkgconfig = 'pkg-config'
{extra_binaries}
'''

SCRIPTDIR = os.path.normpath(os.path.dirname(__file__))


def get_toolchain_prefix(options):
    if options.toolchain_prefix != '':
        return options.toolchain_prefix
    prefix = ''
    if options.cpu_family == "aarch64":
        prefix = 'aarch64-linux-gnu-'
    else:
        if options.target_arch == "arm":
            prefix = 'arm-linux-gnu-'
    return prefix


def get_cflags(options):
    cflags = ' -Wall -g -O2'
    if options.target_arch == "armv7":
        cflags = ' -march=armv7-a '
    cflags = cflags + ' ' + options.custom_cflags
    return cflags


def get_ldflags(options):
    ldflags = ''
    if options.sysroot != '':
        ldflags = '-L{}/lib -Wl,-rpath-link={}/lib'.format(
            options.sysroot, options.sysroot)

    ldflags = ldflags + ' ' + options.custom_ldflags
    return ldflags


def get_subprocess_env(options):
    env = os.environ.copy()
    prefix = get_toolchain_prefix(options)
    cflags = get_cflags(options)
    cxxflags = get_cflags(options)
    ldflags = get_ldflags(options)
    if options.use_clang:
        env['CC'] = 'clang'
        env['CXX'] = 'clang++'
        env['CPP'] = 'clang'
        prefix = ''
    else:
        env['CC'] = prefix + 'gcc'
        env['CXX'] = prefix + 'g++'
        env['CPP'] = prefix + 'cpp'

    env['LD'] = prefix + 'ld'
    env['STRIP'] = prefix + 'strip'
    env['OBJCOPY'] = prefix + 'objcopy'
    env['RANLIB'] = prefix + 'ranlib'
    env['AS'] = prefix + 'as'
    env['AR'] = prefix + 'ar'
    env['NM'] = prefix + 'nm'

    env['CFLAGS'] = cflags
    env['CXXFLAGS'] = cxxflags
    env['OBJCFLAGS'] = cflags
    env['LDFLAGS'] = ldflags
    if options.sysroot != '':
        env['PKG_CONFIG_LIBDIR'] = '{}/lib/pkgconfig:{}/usr/share/pkgconfig'.format(
            options.sysroot, options.sysroot)
    else:
        env['PKG_CONFIG_LIBDIR'] = '__no_cross_sysroot__'

    return env


def check_binaries(bins):
    for b in bins:
        b = str(b[0])
        if not shutil.which(b):
            print("Cannot find '{}' you may have to update your PATH".format(b))


def _write_meson_cross_file(env, options):

    cc = env['CC'].split()
    cxx = env['CXX'].split()
    ar = env['AR'].split()
    strip = env.get('STRIP', '').split()
    windres = env.get('WINDRES', '').split()

    check_binaries([cc, cxx, ar, strip])

    # We do not use cmake dependency files, speed up the build by disabling it
    cross_binaries = {}
    if 'STRIP' in env:
        cross_binaries['strip'] = env['STRIP'].split()
    if 'WINDRES' in env:
        cross_binaries['windres'] = env['WINDRES'].split()
    if 'OBJC' in env:
        cross_binaries['objc'] = env['OBJC'].split()
    if 'OBJCXX' in env:
        cross_binaries['objcpp'] = env['OBJCXX'].split()

    # *FLAGS are only passed to the native compiler, so while
    # cross-compiling we need to pass these through the cross file.
    c_args = shlex.split(env.get('CFLAGS', ''))
    cpp_args = shlex.split(env.get('CXXFLAGS', ''))
    objc_args = shlex.split(env.get('OBJCFLAGS', ''))
    objcpp_args = shlex.split(env.get('OBJCXXFLAGS', ''))
    # Link args
    c_link_args = shlex.split(env.get('LDFLAGS', ''))
    cpp_link_args = c_link_args
    if 'OBJLDFLAGS' in env:
        objc_link_args = shlex.split(env['OBJLDFLAGS'])
    else:
        objc_link_args = c_link_args
    objcpp_link_args = objc_link_args

    pkg_config_libdir = shlex.split(env.get('PKG_CONFIG_LIBDIR', ''))

    # Operate on a copy of the recipe properties to avoid accumulating args
    # from all archs when doing universal builds
    cross_properties = {}  # copy.deepcopy(self.meson_cross_properties)
    for args in ('c_args', 'cpp_args', 'objc_args', 'objcpp_args',
                 'c_link_args', 'cpp_link_args', 'objc_link_args',
                 'objcpp_link_args', 'pkg_config_libdir'):
        if args in cross_properties:
            cross_properties[args] += locals()[args]
        else:
            cross_properties[args] = locals()[args]

    extra_properties = ''
    for k, v in cross_properties.items():
        extra_properties += '{} = {}\n'.format(k, str(v))
    if not options.no_include_sysroot:
        extra_properties += '{} = \'{}\'\n'.format(
            'sys_root', str(options.sysroot))

    extra_binaries = ''
    for k, v in cross_binaries.items():
        extra_binaries += '{} = {}\n'.format(k, str(v))

    check_binaries(cross_binaries.values())

    # Create a cross-info file that tells Meson and GCC how to cross-compile
    # this project
    cross_file = os.path.join(options.cross_file)
    contents = MESON_CROSS_FILE_TPL.format(
        system=options.target_platform,
        cpu=options.target_arch,
        cpu_family=options.cpu_family,
        # Assume all ARM sub-archs are in little endian mode
        endian='little',
        CC=cc,
        CXX=cxx,
        AR=ar,
        extra_binaries=extra_binaries,
        extra_properties=extra_properties)
    with open(cross_file, 'w') as f:
        f.write(contents)

    return cross_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--cross-file", '-c',
                        default='my-meson-cross-file.txt',
                        help="The meson cross-file, default: 'my-meson-cross-file.txt'.")
    parser.add_argument("--toolchain-prefix", '-t',
                        default='',
                        help="The toolchain prefix such as 'arm-linux-gnueabi-', default: ''.")
    parser.add_argument("--custom-cflags", '-C',
                        default='',
                        help="The custom cflags from the toolchain, default: ''.")
    parser.add_argument("--custom-ldflags", '-L',
                        default='',
                        help="The custom ldflags from the toolchain, default: ''.")
    parser.add_argument("--sysroot", '-s',
                        default='',
                        help="The sysroot directory to use, default: ''.")
    parser.add_argument("--target-platform", '-p',
                        default='linux',
                        help="The target platform to use, default: 'linux'.")
    parser.add_argument("--target-arch", '-a',
                        default='arm64',
                        help="The target arch to use, default: 'aarch64'.")
    parser.add_argument("--cpu-family", '-f',
                        default='aarch64',
                        help="The cpu family to use, default: 'arm64'.")
    parser.add_argument("--no-include-sysroot",
                        default=False,
                        action='store_true',
                        help="dot not include sysroot in the cross file.")
    parser.add_argument("--use-clang",
                        default=False,
                        action='store_true',
                        help="dot not include sysroot in the cross file.")

    options = parser.parse_args()

    env = get_subprocess_env(options)

    print("Creating meson cross file with file name '%s' and options:" %
          options.cross_file)
    print("")
    print("\tsysroot: %s" % options.sysroot)
    print("\ttarget platform: %s" % options.target_platform)
    print("\ttarget architecture: %s" % options.target_arch)
    print("\tcpu family: %s" % options.cpu_family)
    print("\ttoolchain-prefix: %s" % get_toolchain_prefix(options))
    print("\tCFLAGS: %s" % get_cflags(options))
    print("\tLDFLAGS: %s" % get_ldflags(options))
    print("")

    cross_file = _write_meson_cross_file(env, options)
    print("The cross file has been written correctly. You can now run 'meson configure --cross-file=%s'" % cross_file)
