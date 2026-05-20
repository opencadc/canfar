"""Cavern storage file management commands for CANFAR CLI."""

from __future__ import annotations

import errno
import glob
import logging
import math
import os
import re
import sys
import time
from typing import Annotated
from urllib.parse import urlparse

import typer
import vos
from cadcutils import exceptions
from vos import md5_cache
from vos.vos import CADC_GMS_PREFIX, SortNodeProperty, convert_vospace_time_to_seconds

from canfar import get_logger, set_log_level
from canfar.hooks.typer.aliases import AliasGroup
from canfar.utils.console import console
from canfar.vospace import StorageClient

log = get_logger(__name__)


storage_cli = typer.Typer(
    name="storage",
    help="Manage files in Cavern storage",
    no_args_is_help=True,
    rich_help_panel="File Management",
    cls=AliasGroup,
)


# Global flag for human-readable sizes (used by formatting functions)
_human_readable = False


def _size_format(size):
    """Format a size value for listing.

    Args:
        size: Size in bytes

    Returns:
        str: Formatted size string
    """
    try:
        size = float(size)
    except Exception as ex:
        log.debug(str(ex))
        size = 0.0

    if _human_readable:
        size_unit = ['B', 'K', 'M', 'G', 'T']
        try:
            length = float(size)
            scale = int(math.log(length) / math.log(1024))
            length = f"{length / (1024.0 ** scale):.0f}{size_unit[scale]}"
        except Exception:
            length = str(int(size))
    else:
        length = str(int(size))
    return f"{length:>12} "


def _date_format(epoch):
    """Given an epoch, return a unix-ls like formatted string.

    Args:
        epoch: Unix timestamp

    Returns:
        str: Formatted date string
    """
    time_tuple = time.localtime(epoch)
    if time.localtime().tm_year != time_tuple.tm_year:
        return time.strftime('%b %d  %Y ', time_tuple)
    return time.strftime('%b %d %H:%M ', time_tuple)


# Mapping of node properties to formatting functions
_LIST_FORMATS = {
    'permissions': lambda value: f"{value:<11}",
    'creator': lambda value: f" {value:<20}",
    'readGroup': lambda value: f" {value.replace(CADC_GMS_PREFIX, ''):<15}",
    'writeGroup': lambda value: f" {value.replace(CADC_GMS_PREFIX, ''):<15}",
    'isLocked': lambda value: f" {['', 'LOCKED'][value == 'true']:<8}",
    'size': _size_format,
    'date': _date_format,
}


def _get_sort_key(node, sort):
    """Get the sort key for a node based on sort type.

    Args:
        node: VOSpace node
        sort: Sort property type

    Returns:
        Comparable value for sorting
    """
    if sort == SortNodeProperty.LENGTH:
        return int(node.props['length'])
    elif sort == SortNodeProperty.DATE:
        return convert_vospace_time_to_seconds(node.props['date'])
    else:
        return node.name


def _display_target(columns, row):
    """Display a VOSpace node with specified columns.

    Args:
        columns: List of column names to display
        row: VOSpace node to display
    """
    name_string = row.name
    info = row.get_info()

    for col in columns:
        value = info.get(col, None)
        value = value if value is not None else ""
        if col in _LIST_FORMATS:
            sys.stdout.write(_LIST_FORMATS[col](value))

    if info["permissions"][0] == 'l':
        name_string = f"{row.name} -> {info['target']}"

    sys.stdout.write(f"{name_string}\n")


@storage_cli.command("ls")
def list_files(
    uri: Annotated[
        str,
        typer.Argument(help="Cavern path to list (e.g., vos:, vos:/dir)"),
    ],
    long: Annotated[
        bool,
        typer.Option("--long", "-l", help="Verbose listing sorted by name"),
    ] = False,
    group: Annotated[
        bool,
        typer.Option("--group", "-g", help="Display group read/write information"),
    ] = False,
    human: Annotated[
        bool,
        typer.Option("--human", "-h", help="Make sizes human readable"),
    ] = False,
    size_sort: Annotated[
        bool,
        typer.Option("--Size", "-S", help="Sort files by size"),
    ] = False,
    reverse: Annotated[
        bool,
        typer.Option("--reverse", "-r", help="Reverse the sort order"),
    ] = False,
    time_sort: Annotated[
        bool,
        typer.Option("--time", "-t", help="Sort by time copied to Cavern"),
    ] = False,
    debug: Annotated[
        bool,
        typer.Option("--debug", help="Enable debug logging"),
    ] = False,
) -> None:
    """List Cavern directory contents.

    Lists information about a Cavern DataNode or the contents of a ContainerNode.

    Examples:
        canfar storage ls vos:
        canfar storage ls -l vos:/data/
        canfar storage ls -lh vos:/data/*.fits
    """
    if debug:
        set_log_level("DEBUG")

    global _human_readable
    _human_readable = human

    try:
        client_obj = StorageClient()
        client = client_obj.storage_client

        # Set which columns will be printed
        columns = []
        if long or group:
            columns = ['permissions']
            if long:
                columns.extend(['creator'])
            columns.extend(['readGroup', 'writeGroup', 'isLocked', 'size', 'date'])

        files = []
        dirs = []

        # Determine if there is a sorting order
        if size_sort:
            sort = SortNodeProperty.LENGTH
        elif time_sort:
            sort = SortNodeProperty.DATE
        else:
            sort = None

        if sort is None and reverse is False:
            order = None
        elif reverse:
            order = 'asc' if sort else 'desc'
        else:
            order = 'desc' if sort else 'asc'

        if not client.is_remote_file(file_name=uri):
            console.print(f"[bold red]Error: Invalid Cavern node name: {uri}[/bold red]")
            raise typer.Exit(1)

        log.debug(f"Getting listing of: {uri}")

        targets = client.glob(uri)

        # Segregate files from directories
        for target in targets:
            target_node = client.get_node(target)
            if not long or target.endswith('/'):
                while target_node.islink():
                    target_node = client.get_node(target_node.target)
            if target_node.isdir():
                dirs.append((_get_sort_key(target_node, sort), target_node, target))
            else:
                files.append((_get_sort_key(target_node, sort), target_node))

        # Display files
        for f in sorted(files, key=lambda ff: ff[0], reverse=(order == 'desc')):
            _display_target(columns, f[1])

        # Display directories
        for d in sorted(dirs, key=lambda dd: dd[0], reverse=(order == 'desc')):
            n = d[1]
            if (len(dirs) + len(files)) > 1:
                sys.stdout.write(f'\n{n.name}:\n')
                if long:
                    sys.stdout.write(f'total: {int(n.get_info()["size"])}\n')
            for row in client.get_children_info(d[2], sort, order):
                _display_target(columns, row)

    except Exception as ex:
        console.print(f"[bold red]Error: {ex}[/bold red]")
        raise typer.Exit(1) from ex


@storage_cli.command("cp")
def copy_files(
    source: Annotated[
        list[str],
        typer.Argument(help="Source file(s)/directory to copy from"),
    ],
    destination: Annotated[
        str,
        typer.Argument(help="Destination file/directory to copy to"),
    ],
    exclude: Annotated[
        str | None,
        typer.Option("--exclude", help="Skip files matching pattern (overrides include)"),
    ] = None,
    include: Annotated[
        str | None,
        typer.Option("--include", help="Only copy files matching pattern"),
    ] = None,
    interrogate: Annotated[
        bool,
        typer.Option("-i", "--interrogate", help="Ask before overwriting files"),
    ] = False,
    follow_links: Annotated[
        bool,
        typer.Option("-L", "--follow-links", help="Follow symbolic links"),
    ] = False,
    ignore: Annotated[
        bool,
        typer.Option("--ignore", help="Ignore errors and continue with recursive copy"),
    ] = False,
    head: Annotated[
        bool,
        typer.Option("--head", help="Copy only the headers of a file from Cavern"),
    ] = False,
    debug: Annotated[
        bool,
        typer.Option("--debug", help="Enable debug logging"),
    ] = False,
) -> None:
    """Copy files to and from Cavern storage.

    Copy is always recursive. Supports wildcards and cutouts.

    Examples:
        canfar storage cp myfile.txt vos:/data/
        canfar storage cp vos:/data/*.fits ./local_dir/
        canfar storage cp -i local_dir/ vos:/backup/
    """
    if debug:
        set_log_level("DEBUG")

    class Nonlocal:
        """Workaround for nonlocal scope."""
        exit_code = 0

    dest = destination
    this_destination = dest

    try:
        client_obj = StorageClient()
        client = client_obj.storage_client

        if not client.is_remote_file(dest):
            dest = os.path.abspath(dest)

        cutout_pattern = re.compile(
            r'(.*?)(?P<cutout>(\[[\-+]?[\d*]+(:[\-+]?[\d*]+)?'
            r'(,[\-+]?[\d*]+(:[\-+]?[\d*]+)?)?\])+)$')

        ra_dec_cutout_pattern = re.compile(
            r"([^()]*?)"
            r"(?P<cutout>\("
            r"(?P<ra>[\-+]?\d*(\.\d*)?),"
            r"(?P<dec>[\-+]?\d*(\.\d*)?),"
            r"(?P<rad>\d*(\.\d*)?)\))?")

        def get_node(filename, limit=None):
            """Get node, from cache if possible."""
            return client.get_node(filename, limit=limit)

        def isdir(filename):
            """Check if filename is a directory."""
            log.debug(f"Checking isdir on {filename}")
            if client.is_remote_file(filename):
                return client.isdir(filename)
            else:
                return os.path.isdir(filename)

        def islink(filename):
            """Check if filename is a symbolic link."""
            log.debug(f"Checking islink on {filename}")
            if client.is_remote_file(filename):
                try:
                    return get_node(filename).islink()
                except exceptions.NotFoundException:
                    return False
            else:
                return os.path.islink(filename)

        def access(filename, mode):
            """Check if the file can be accessed."""
            log.debug(f"Checking access for {filename}")
            if client.is_remote_file(filename):
                try:
                    node = get_node(filename, limit=0)
                    return node is not None
                except (exceptions.NotFoundException, exceptions.ForbiddenException,
                        exceptions.UnauthorizedException):
                    return False
            else:
                return os.access(filename, mode)

        def listdir(dirname):
            """Walk through the directory structure."""
            log.debug(f"Getting dirlist for {dirname}")
            if client.is_remote_file(dirname):
                return client.listdir(dirname, force=True)
            else:
                return os.listdir(dirname)

        def mkdir(filename):
            """Create directory."""
            log.debug(f"Making directory {filename}")
            if client.is_remote_file(filename):
                return client.mkdir(filename)
            else:
                return os.mkdir(filename)

        def lglob(pathname):
            """Glob for local or remote files."""
            if client.is_remote_file(pathname):
                return client.glob(pathname)
            else:
                return glob.glob(pathname)

        def copy_file(source_name, destination_name, exclude_arg=None,
                     include_arg=None, interrogate_arg=False, overwrite=False,
                     ignore_arg=False, head_arg=False):
            """Send source_name to destination, possibly looping over contents."""
            try:
                if not follow_links and islink(source_name):
                    log.info(f"{source_name}: Skipping (symbolic link)")
                    return

                if isdir(source_name):
                    # Make sure the destination exists
                    if not isdir(destination_name):
                        mkdir(destination_name)
                    # Copy all files in the current source directory
                    for filename in listdir(source_name):
                        log.debug(f"{filename} -> {source_name}")
                        copy_file(
                            os.path.join(source_name, filename),
                            os.path.join(destination_name, filename),
                            exclude_arg, include_arg, interrogate_arg,
                            overwrite, ignore_arg, head_arg)
                else:
                    if interrogate_arg:
                        if access(destination_name, os.F_OK):
                            ans = typer.prompt(
                                f"File {destination_name} exists. Overwrite? (y/n)",
                                default="n")
                            if ans != 'y':
                                raise Exception("File exists")

                    skip = False
                    if exclude_arg is not None:
                        for pattern in exclude_arg.split(','):
                            if pattern in destination_name:
                                skip = True
                                continue

                    if include_arg is not None:
                        skip = True
                        for pattern in include_arg.split(','):
                            if pattern in destination_name:
                                skip = False
                                continue

                    if not skip:
                        console.print(f"{source_name} -> {destination_name}")

                    niters = 0
                    while not skip:
                        try:
                            log.debug("Starting copy operation")
                            client.copy(source_name, destination_name, head=head_arg)
                            log.debug("Copy operation completed")
                            break
                        except Exception as client_exception:
                            log.debug(f"Copy exception: {client_exception}")
                            if getattr(client_exception, 'errno', -1) == 104:
                                # Connection reset by peer - retry
                                log.warning(str(client_exception))
                                Nonlocal.exit_code += getattr(client_exception, 'errno', -1)
                            elif getattr(client_exception, 'errno', -1) == errno.EIO:
                                # Retry on IO errors
                                log.warning(f"{client_exception}: Retrying")
                                pass
                            elif ignore_arg:
                                if niters > 100:
                                    log.error(
                                        f"{client_exception} (skipping after {niters} attempts)")
                                    skip = True
                                else:
                                    log.error(f"{client_exception} (retrying)")
                                    time.sleep(5)
                                    niters += 1
                            else:
                                raise client_exception

            except OSError as os_exception:
                log.debug(str(os_exception))
                if getattr(os_exception, 'errno', -1) == errno.EINVAL:
                    # Not a valid URI, skip
                    log.warning(f"{os_exception}: Skipping")
                    Nonlocal.exit_code += getattr(os_exception, 'errno', -1)
                else:
                    raise

        # Main copy loop
        for source_pattern in source:
            if head and not client.is_remote_file(source_pattern):
                log.error("--head only works for source files in Cavern")
                continue

            # Handle cutouts
            if not client.is_remote_file(source_pattern):
                sources = [source_pattern]
            else:
                cutout_match = cutout_pattern.search(source_pattern)
                cutout = None
                if cutout_match is not None:
                    source_pattern = cutout_match.group(1)
                    cutout = cutout_match.group('cutout')
                else:
                    ra_dec_match = ra_dec_cutout_pattern.search(source_pattern)
                    if ra_dec_match is not None:
                        cutout = ra_dec_match.group('cutout')

                log.debug(f"Cutout: {cutout}")
                sources = lglob(source_pattern)
                if cutout is not None:
                    sources = [s + cutout for s in sources]

            for source_arg in sources:
                if not client.is_remote_file(source_arg):
                    source_arg = os.path.abspath(source_arg)

                # Source must exist
                if not access(source_arg, os.R_OK):
                    raise Exception(f"Can't access source: {source_arg}")

                if not follow_links and islink(source_arg):
                    log.info(f"{source_arg}: Skipping (symbolic link)")
                    continue

                # Cavern to Cavern copy not yet implemented
                if client.is_remote_file(source_arg) and client.is_remote_file(dest):
                    raise Exception("Cannot (yet) copy from Cavern to Cavern")

                this_destination = dest
                if isdir(source_arg):
                    if not follow_links and islink(source_arg):
                        continue
                    log.debug(f"{source_arg} is a directory or link to one")

                    # Unix behavior: if dest exists, copy into it
                    if access(dest, os.F_OK):
                        if not isdir(dest):
                            raise Exception(
                                f"Can't write a directory ({source_arg}) to a file ({dest})")
                        this_destination = os.path.normpath(
                            os.path.join(dest, os.path.basename(source_arg)))
                    elif len(source) > 1:
                        raise Exception(
                            f"Cannot copy multiple things into non-existent location ({dest})")

                elif dest[-1] == '/' or isdir(dest):
                    # Copying into a directory
                    this_destination = os.path.join(dest, os.path.basename(source_arg))

                copy_file(source_arg, this_destination, exclude_arg=exclude,
                         include_arg=include, interrogate_arg=interrogate,
                         overwrite=False, ignore_arg=ignore, head_arg=head)

    except KeyboardInterrupt as ke:
        log.info("Received keyboard interrupt. Execution aborted.")
        Nonlocal.exit_code = getattr(ke, 'errno', -1)
    except Exception as e:
        if re.search('NodeLocked', str(e)) is not None:
            msg = f"Use vlock to unlock the node before copying to {this_destination}."
            console.print(f"[bold red]Error: {e}[/bold red]")
            console.print(f"[yellow]{msg}[/yellow]")
        elif getattr(e, 'errno', -1) == errno.EREMOTE:
            msg = f"Failure at remote server while copying {source[0]} -> {dest}"
            console.print(f"[bold red]Error: {e}[/bold red]")
            console.print(f"[yellow]{msg}[/yellow]")
        else:
            console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(1) from e

    if Nonlocal.exit_code:
        raise typer.Exit(Nonlocal.exit_code)


@storage_cli.command("rm")
def remove_files(
    node: Annotated[
        list[str],
        typer.Argument(help="Cavern file(s) or directory to delete"),
    ],
    recursive: Annotated[
        bool,
        typer.Option("-R", "--recursive", help="Delete directory even if not empty"),
    ] = False,
    debug: Annotated[
        bool,
        typer.Option("--debug", help="Enable debug logging"),
    ] = False,
) -> None:
    """Remove Cavern files or directories.

    Fails if trying to delete a non-empty container without --recursive flag,
    or if the node is locked.

    Examples:
        canfar storage rm vos:/data/file.txt
        canfar storage rm -R vos:/data/old_dir/
    """
    if debug:
        set_log_level("DEBUG")

    try:
        client_obj = StorageClient()
        client = client_obj.storage_client

        for node_path in node:
            if not client.is_remote_file(node_path):
                console.print(
                    f"[bold red]Error: {node_path} is not a valid Cavern handle[/bold red]")
                raise typer.Exit(1)

            if recursive:
                successes, failures = client.recursive_delete(node_path)
                if failures:
                    console.print(
                        f"[yellow]Warning: deleted {successes}, failed {failures}[/yellow]")
                    raise typer.Exit(1)
                else:
                    console.print(f"[green]Deleted {successes} node(s)[/green]")
            else:
                if not node_path.endswith('/'):
                    if client.get_node(node_path).islink():
                        log.info(f"Deleting link {node_path}")
                        client.delete(node_path)
                        console.print(f"[green]Deleted link {node_path}[/green]")
                    elif client.isfile(node_path):
                        log.info(f"Deleting {node_path}")
                        client.delete(node_path)
                        console.print(f"[green]Deleted {node_path}[/green]")
                elif client.isdir(node_path):
                    console.print(
                        f"[bold red]Error: {node_path} is a directory "
                        f"(use -R for recursive delete)[/bold red]")
                    raise typer.Exit(1)
                else:
                    console.print(
                        f"[bold red]Error: {node_path} is not a directory[/bold red]")
                    raise typer.Exit(1)

    except Exception as ex:
        console.print(f"[bold red]Error: {ex}[/bold red]")
        raise typer.Exit(1) from ex


@storage_cli.command("mkdir")
def make_directory(
    container_node: Annotated[
        str,
        typer.Argument(help="Cavern directory path to create"),
    ],
    parents: Annotated[
        bool,
        typer.Option("-p", "--parents", help="Create intermediate directories as required"),
    ] = False,
    debug: Annotated[
        bool,
        typer.Option("--debug", help="Enable debug logging"),
    ] = False,
) -> None:
    """Create a new Cavern directory (ContainerNode).

    Examples:
        canfar storage mkdir vos:/data/new_dir
        canfar storage mkdir -p vos:/data/path/to/new_dir
    """
    if debug:
        set_log_level("DEBUG")

    log.info(f"Creating ContainerNode (directory) {container_node}")

    try:
        client_obj = StorageClient()
        client = client_obj.storage_client

        this_dir = container_node

        dir_names = []
        if parents:
            while not client.access(this_dir):
                dir_names.append(os.path.basename(this_dir))
                this_dir = os.path.dirname(this_dir)
            while len(dir_names) > 0:
                this_dir = os.path.join(this_dir, dir_names.pop())
                client.mkdir(this_dir)
                console.print(f"[green]Created {this_dir}[/green]")
        else:
            client.mkdir(this_dir)
            console.print(f"[green]Created {container_node}[/green]")

    except Exception as ex:
        console.print(f"[bold red]Error: {ex}[/bold red]")
        raise typer.Exit(1) from ex


@storage_cli.command("mv")
def move_node(
    source: Annotated[
        str,
        typer.Argument(help="Cavern node to move"),
    ],
    destination: Annotated[
        str,
        typer.Argument(help="Cavern destination path"),
    ],
    debug: Annotated[
        bool,
        typer.Option("--debug", help="Enable debug logging"),
    ] = False,
) -> None:
    """Move or rename a Cavern node.

    If destination is a container, move source into it.
    Otherwise, rename source to destination.

    Examples:
        canfar storage mv vos:/data/old.txt vos:/data/new.txt
        canfar storage mv vos:/data/file.txt vos:/archive/
    """
    if debug:
        set_log_level("DEBUG")

    try:
        client_obj = StorageClient()
        client = client_obj.storage_client

        if not client.is_remote_file(source):
            console.print(f"[bold red]Error: Source {source} is not a remote node[/bold red]")
            raise typer.Exit(1)

        if not client.is_remote_file(destination):
            console.print(
                f"[bold red]Error: Destination {destination} is not a remote node[/bold red]")
            raise typer.Exit(1)

        if urlparse(source).scheme != urlparse(destination).scheme:
            console.print("[bold red]Error: Move between services not supported[/bold red]")
            raise typer.Exit(1)

        log.info(f"{source} -> {destination}")
        client.move(source, destination)
        console.print(f"[green]Moved {source} -> {destination}[/green]")

    except Exception as ex:
        console.print(f"[bold red]Error: {ex}[/bold red]")
        raise typer.Exit(1) from ex

