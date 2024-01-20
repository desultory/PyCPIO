#!/usr/bin/env python3

from pathlib import Path

from pycpio import PyCPIO
from zenlib.util import get_kwargs_from_args, get_args_n_logger


def main():
    arguments = [{'flags': ['-i', '--input'], 'help': 'input file'},
                 {'flags': ['-a', '--append'], 'help': 'append to archive'},
                 {'flags': ['--recursive'], 'action': 'store_true', 'help': 'append to archive recursively'},
                 {'flags': ['--relative'], 'action': 'store', 'help': 'append to archive relative to this path'},
                 {'flags': ['--absolute'], 'action': 'store_true', 'help': 'allow absolute paths'},
                 {'flags': ['--rm', '--delete'], 'action': 'store', 'help': 'delete from archive'},
                 {'flags': ['-n', '--name'], 'action': 'store', 'help': 'Name/path override for append'},
                 {'flags': ['-s', '--symlink'], 'action': 'store', 'help': 'create symlink'},
                 {'flags': ['-c', '--chardev'], 'action': 'store', 'help': 'create character device'},
                 {'flags': ['--major'], 'action': 'store', 'help': 'major number for character/block device', 'type': int},
                 {'flags': ['--minor'], 'action': 'store', 'help': 'minor number for character/block device', 'type': int},
                 {'flags': ['-u', '--set-owner'], 'action': 'store', 'help': 'set UID on all files', 'type': int, 'dest': 'uid'},
                 {'flags': ['-g', '--set-group'], 'action': 'store', 'help': 'set GID on all files', 'type': int, 'dest': 'gid'},
                 {'flags': ['-m', '--set-mode'], 'action': 'store', 'help': 'set mode on all files', 'type': int, 'dest': 'mode'},
                 {'flags': ['-o', '--output'], 'help': 'output file'},
                 {'flags': ['-l', '--list'], 'action': 'store_true', 'help': 'list CPIO contents'},
                 {'flags': ['-p', '--print'], 'action': 'store_true', 'help': 'print CPIO contents'}]

    args, logger = get_args_n_logger(package=__package__, description='PyCPIO', arguments=arguments)
    kwargs = get_kwargs_from_args(args, logger=logger)

    c = PyCPIO(**kwargs)
    if args.input:
        c.read_cpio_file(Path(args.input))

    if args.rm:
        c.remove_cpio(args.rm)

    if args.symlink:
        if not args.name:
            raise ValueError('Symlink requires a name')
        c.add_symlink(args.name, args.symlink)

    if args.chardev:
        if not args.major or not args.minor:
            raise ValueError('Character device requires major and minor numbers')
        c.add_chardev(args.chardev, int(args.major), int(args.minor))

    if args.append:
        relative = args.relative if args.relative else None
        cmdargs = {'relative': relative, 'path': Path(args.append)}

        if args.name:
            cmdargs['name'] = args.name

        if args.absolute:
            cmdargs['absolute'] = args.absolute

        if args.recursive:
            c.append_recursive(**cmdargs)
        else:
            c.append_cpio(**cmdargs)

    if args.output:
        c.write_cpio_file(Path(args.output))

    if args.list:
        print(c.list_files())

    if args.print:
        print(c)


if __name__ == '__main__':
    main()
