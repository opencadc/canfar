"""VOSpace file management commands for CANFAR CLI."""

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
from canfar.client import HTTPClient
from canfar.hooks.typer.aliases import AliasGroup
from canfar.utils.console import console

log = get_logger(__name__)


vos_cli = typer.Typer(
    name="vos",
    help="Manage files in VOSpace",
    no_args_is_help=True,
    rich_help_panel="File Management",
    cls=AliasGroup,
)


class VOSpaceClient(HTTPClient):
    """VOSpace client that inherits authentication from HTTPClient.

    This client automatically uses the active CANFAR authentication context
    to create an authenticated vos.Client instance.
    """

    def __init__(self, **kwargs):
        """Initialize VOSpaceClient with HTTPClient authentication."""
        super().__init__(**kwargs)
        self._vos_client = None

    @property
    def vos_client(self) -> vos.Client:
        """Get or create authenticated vos.Client instance.

        Returns:
            vos.Client: Authenticated VOSpace client using the active context's token.
        """
        if self._vos_client is None:
            # Extract token from active authentication context
            ctx = self.config.context

            # Get access token based on auth mode
            if hasattr(ctx, 'token') and ctx.token:
                token = ctx.token.access
            else:
                # Fallback for X509 or other auth modes
                token = None

            self._vos_client = vos.Client(vospace_token=token)

        return self._vos_client


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


@vos_cli.command("ls")
def list_files(
    uri: Annotated[
        str,
        typer.Argument(help="VOSpace path to list (e.g., vos:, vos:/dir)"),
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
        typer.Option("--time", "-t", help="Sort by time copied to VOSpace"),
    ] = False,
    debug: Annotated[
        bool,
        typer.Option("--debug", help="Enable debug logging"),
    ] = False,
) -> None:
    """List VOSpace directory contents.

    Lists information about a VOSpace DataNode or the contents of a ContainerNode.

    Examples:
        canfar vos ls vos:
        canfar vos ls -l vos:/data/
        canfar vos ls -lh vos:/data/*.fits
    """
    if debug:
        set_log_level("DEBUG")

    global _human_readable
    _human_readable = human

    try:
        client_obj = VOSpaceClient()
        client = client_obj.vos_client

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
            console.print(f"[bold red]Error: Invalid VOSpace node name: {uri}[/bold red]")
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


@vos_cli.command("cp")
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
        typer.Option("--head", help="Copy only the headers of a file from VOSpace"),
    ] = False,
    debug: Annotated[
        bool,
        typer.Option("--debug", help="Enable debug logging"),
    ] = False,
) -> None:
    """Copy files to and from VOSpace.

    Copy is always recursive. Supports wildcards and cutouts.

    Examples:
        canfar vos cp myfile.txt vos:/data/
        canfar vos cp vos:/data/*.fits ./local_dir/
        canfar vos cp -i local_dir/ vos:/backup/
    """
    if debug:
        set_log_level("DEBUG")

    class Nonlocal:
        """Workaround for nonlocal scope."""
        exit_code = 0

    dest = destination
    this_destination = dest

    try:
        client_obj = VOSpaceClient()
        client = client_obj.vos_client

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
                log.error("--head only works for source files in VOSpace")
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

                # VOSpace to VOSpace copy not yet implemented
                if client.is_remote_file(source_arg) and client.is_remote_file(dest):
                    raise Exception("Cannot (yet) copy from VOSpace to VOSpace")

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


@vos_cli.command("rm")
def remove_files(
    node: Annotated[
        list[str],
        typer.Argument(help="VOSpace file(s) or directory to delete"),
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
    """Remove VOSpace files or directories.

    Fails if trying to delete a non-empty container without --recursive flag,
    or if the node is locked.

    Examples:
        canfar vos rm vos:/data/file.txt
        canfar vos rm -R vos:/data/old_dir/
    """
    if debug:
        set_log_level("DEBUG")

    try:
        client_obj = VOSpaceClient()
        client = client_obj.vos_client

        for node_path in node:
            if not client.is_remote_file(node_path):
                console.print(
                    f"[bold red]Error: {node_path} is not a valid VOSpace handle[/bold red]")
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


@vos_cli.command("mkdir")
def make_directory(
    container_node: Annotated[
        str,
        typer.Argument(help="VOSpace directory path to create"),
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
    """Create a new VOSpace directory (ContainerNode).

    Examples:
        canfar vos mkdir vos:/data/new_dir
        canfar vos mkdir -p vos:/data/path/to/new_dir
    """
    if debug:
        set_log_level("DEBUG")

    log.info(f"Creating ContainerNode (directory) {container_node}")

    try:
        client_obj = VOSpaceClient()
        client = client_obj.vos_client

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


@vos_cli.command("mv")
def move_node(
    source: Annotated[
        str,
        typer.Argument(help="VOSpace node to move"),
    ],
    destination: Annotated[
        str,
        typer.Argument(help="VOSpace destination path"),
    ],
    debug: Annotated[
        bool,
        typer.Option("--debug", help="Enable debug logging"),
    ] = False,
) -> None:
    """Move or rename a VOSpace node.

    If destination is a container, move source into it.
    Otherwise, rename source to destination.

    Examples:
        canfar vos mv vos:/data/old.txt vos:/data/new.txt
        canfar vos mv vos:/data/file.txt vos:/archive/
    """
    if debug:
        set_log_level("DEBUG")

    try:
        client_obj = VOSpaceClient()
        client = client_obj.vos_client

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


@vos_cli.command("cat")
def cat_file(
    uri: Annotated[
        str,
        typer.Argument(help="VOSpace file to display"),
    ],
    head: Annotated[
        bool,
        typer.Option("--head", help="Display only the header"),
    ] = False,
    debug: Annotated[
        bool,
        typer.Option("--debug", help="Enable debug logging"),
    ] = False,
) -> None:
    """Display contents of a VOSpace file.

    Streams the file content to stdout.

    Examples:
        canfar vos cat vos:/data/file.txt
        canfar vos cat --head vos:/data/image.fits
    """
    if debug:
        set_log_level("DEBUG")

    try:
        client_obj = VOSpaceClient()
        client = client_obj.vos_client

        if not client.is_remote_file(uri):
            console.print(f"[bold red]Error: {uri} is not a valid VOSpace file[/bold red]")
            raise typer.Exit(1)

        view = 'header' if head else 'data'
        with client.open(uri, view=view) as fh:
            content = fh.read(return_response=True).text
            sys.stdout.write(content)
            if not content.endswith('\n'):
                sys.stdout.write('\n')

    except Exception as ex:
        console.print(f"[bold red]Error: {ex}[/bold red]")
        raise typer.Exit(1) from ex


@vos_cli.command("ln")
def link_node(
    source: Annotated[
        str,
        typer.Argument(help="Source location (can be vos:, https:, or file: URI)"),
    ],
    target: Annotated[
        str,
        typer.Argument(help="Target VOSpace LinkNode to create"),
    ],
    debug: Annotated[
        bool,
        typer.Option("--debug", help="Enable debug logging"),
    ] = False,
) -> None:
    """Create a symbolic link in VOSpace.

    Creates a LinkNode that points to another location. The source can be
    a VOSpace node, an external URL, or a local file.

    Examples:
        canfar vos ln vos:/data/original.txt vos:/data/link.txt
        canfar vos ln https://example.com/data.fits vos:/data/external_link
        canfar vos ln file:///local/file.txt vos:/data/local_link
    """
    if debug:
        set_log_level("DEBUG")

    try:
        client_obj = VOSpaceClient()
        client = client_obj.vos_client

        if not client.is_remote_file(target):
            console.print(
                f"[bold red]Error: Target {target} must be a VOSpace node[/bold red]")
            raise typer.Exit(1)

        client.link(source, target)
        console.print(f"[green]Created link {target} -> {source}[/green]")

    except Exception as ex:
        console.print(f"[bold red]Error: {ex}[/bold red]")
        raise typer.Exit(1) from ex


@vos_cli.command("lock")
def lock_node(
    node: Annotated[
        str,
        typer.Argument(help="VOSpace node to lock/unlock/check"),
    ],
    lock: Annotated[
        bool,
        typer.Option("--lock", help="Lock the node (prevents modifications)"),
    ] = False,
    unlock: Annotated[
        bool,
        typer.Option("--unlock", help="Unlock the node"),
    ] = False,
    debug: Annotated[
        bool,
        typer.Option("--debug", help="Enable debug logging"),
    ] = False,
) -> None:
    """Lock, unlock, or check lock status of a VOSpace node.

    A locked node cannot be copied to, moved, or deleted.
    Without --lock or --unlock, displays the current lock status.

    Examples:
        canfar vos lock vos:/data/important.txt --lock
        canfar vos lock vos:/data/important.txt --unlock
        canfar vos lock vos:/data/important.txt
    """
    if debug:
        set_log_level("DEBUG")

    if lock and unlock:
        console.print("[bold red]Error: Cannot specify both --lock and --unlock[/bold red]")
        raise typer.Exit(1)

    try:
        client_obj = VOSpaceClient()
        client = client_obj.vos_client

        node_obj = client.get_node(node)

        if lock or unlock:
            # Set lock state
            node_obj.is_locked = lock and not unlock
            client.update(node_obj)
            state = "locked" if node_obj.is_locked else "unlocked"
            console.print(f"[green]Node {node} is now {state}[/green]")
        else:
            # Display lock status
            if node_obj.is_locked:
                console.print(f"[yellow]Node {node} is LOCKED[/yellow]")
            else:
                console.print(f"[green]Node {node} is unlocked[/green]")

    except Exception as ex:
        console.print(f"[bold red]Error: {ex}[/bold red]")
        raise typer.Exit(1) from ex


@vos_cli.command("chmod")
def change_mode(
    mode: Annotated[
        str,
        typer.Argument(
            help="Permission mode: (o|g|og)[+|-|=](r|w|rw). "
                 "o=other/public, g=group, r=read, w=write"
        ),
    ],
    node: Annotated[
        str,
        typer.Argument(help="VOSpace node to modify"),
    ],
    groups: Annotated[
        list[str],
        typer.Argument(help="Group name(s) for group permissions (up to 4)"),
    ] = None,
    recursive: Annotated[
        bool,
        typer.Option("-R", "--recursive", help="Apply permissions recursively"),
    ] = False,
    debug: Annotated[
        bool,
        typer.Option("--debug", help="Enable debug logging"),
    ] = False,
) -> None:
    """Change read/write permissions on VOSpace nodes.

    Permission modes:
    - o+r / o-r : Make public / Make private
    - g+r / g-r : Add/remove group read permission
    - g+w / g-w : Add/remove group write permission
    - g+rw : Add group read and write permissions

    When adding group permissions, specify group names as additional arguments.

    Examples:
        canfar vos chmod o+r vos:/data/file.txt
        canfar vos chmod g+r vos:/data/file.txt Group1 Group2
        canfar vos chmod g-rw vos:/data/file.txt
        canfar vos chmod o+r vos:/data/ -R
    """
    if debug:
        set_log_level("DEBUG")

    # Parse mode string
    mode_pattern = re.compile(r"(?P<who>og|go|o|g)(?P<op>[+\-=])(?P<what>rw|wr|r|w)")
    mode_match = mode_pattern.match(mode)

    if not mode_match:
        console.print(f"[bold red]Error: Invalid mode '{mode}'. "
                     f"Use format: (o|g|og)[+|-|=](r|w|rw)[/bold red]")
        raise typer.Exit(1)

    mode_dict = mode_match.groupdict()
    who = mode_dict['who']
    op = mode_dict['op']
    what = mode_dict['what']

    try:
        client_obj = VOSpaceClient()
        client = client_obj.vos_client

        props = {}

        # Handle 'other' (public) permissions
        if 'o' in who:
            if op == '-':
                props['ispublic'] = 'false'
            else:
                props['ispublic'] = 'true'

        # Handle group permissions
        if 'g' in who:
            if op == '-':
                # Remove group permissions
                if 'r' in what:
                    props['readgroup'] = None
                if 'w' in what:
                    props['writegroup'] = None
            else:
                # Add group permissions
                if not groups:
                    console.print(
                        "[bold red]Error: Group names required when adding "
                        "group permissions[/bold red]")
                    raise typer.Exit(1)

                if len(groups) > 4:
                    console.print(
                        "[bold red]Error: Maximum 4 groups can be specified[/bold red]")
                    raise typer.Exit(1)

                # Prefix groups with CADC_GMS_PREFIX if needed
                from vos.vos import CADC_GMS_PREFIX
                prefixed_groups = [
                    g if g.startswith(CADC_GMS_PREFIX) else f"{CADC_GMS_PREFIX}{g}"
                    for g in groups
                ]
                group_list = " ".join(prefixed_groups)

                if 'r' in what:
                    props['readgroup'] = group_list
                if 'w' in what:
                    props['writegroup'] = group_list

        # Apply the changes
        if recursive:
            client.set_property_recursive(node, props)
            console.print(f"[green]Recursively updated permissions on {node}[/green]")
        else:
            node_obj = client.get_node(node)
            client.update(node_obj, props)
            console.print(f"[green]Updated permissions on {node}[/green]")

    except Exception as ex:
        console.print(f"[bold red]Error: {ex}[/bold red]")
        raise typer.Exit(1) from ex


@vos_cli.command("tag")
def manage_tags(
    node: Annotated[
        str,
        typer.Argument(help="VOSpace node to manage properties on"),
    ],
    properties: Annotated[
        list[str],
        typer.Argument(help="Property operations: key=value to set, key to read, key= to delete"),
    ] = None,
    remove: Annotated[
        bool,
        typer.Option("--remove", help="Remove the specified properties"),
    ] = False,
    recursive: Annotated[
        bool,
        typer.Option("-R", "--recursive", help="Apply operation recursively"),
    ] = False,
    debug: Annotated[
        bool,
        typer.Option("--debug", help="Enable debug logging"),
    ] = False,
) -> None:
    """Manage properties (tags/attributes) on VOSpace nodes.

    Properties are key-value pairs stored as node metadata.
    Only user-defined properties can be set or removed.

    Operations:
    - Set: key=value
    - Read: key (displays value)
    - Delete: key= or key with --remove
    - List all: no property argument

    Examples:
        canfar vos tag vos:/data/file.fits quality=good
        canfar vos tag vos:/data/file.fits quality
        canfar vos tag vos:/data/file.fits quality=
        canfar vos tag vos:/data/file.fits quality --remove
        canfar vos tag vos:/data/file.fits
        canfar vos tag vos:/data/ quality=verified -R
    """
    if debug:
        set_log_level("DEBUG")

    try:
        client_obj = VOSpaceClient()
        client = client_obj.vos_client

        node_obj = client.get_node(node, limit=None, force=True)

        # No properties specified - list all properties
        if not properties:
            all_props = node_obj.props
            if all_props:
                console.print(f"\n[bold]Properties for {node}:[/bold]")
                for key, value in sorted(all_props.items()):
                    console.print(f"  {key} = {value}")
            else:
                console.print(f"[yellow]No properties found on {node}[/yellow]")
            return

        # Parse property operations
        props_to_set = {}
        props_to_read = []
        props_to_delete = []

        if remove:
            # All properties should be marked for deletion
            props_to_delete = [p if '=' not in p else p.split('=')[0] for p in properties]
        else:
            for prop in properties:
                if '=' in prop:
                    key, value = prop.split('=', 1)
                    if value == '':
                        # Delete property
                        props_to_delete.append(key)
                    else:
                        # Set property
                        props_to_set[key] = value
                else:
                    # Read property
                    props_to_read.append(prop)

        # Read properties
        for prop_name in props_to_read:
            value = node_obj.props.get(prop_name)
            if value is not None:
                console.print(f"{prop_name} = {value}")
            else:
                console.print(f"[yellow]Property '{prop_name}' not found[/yellow]")

        # Set or delete properties
        if props_to_set or props_to_delete:
            # Prepare properties dict
            update_props = props_to_set.copy()
            for prop_name in props_to_delete:
                update_props[prop_name] = None  # None value deletes the property

            if recursive:
                client.set_property_recursive(node, update_props)
                console.print(f"[green]Recursively updated properties on {node}[/green]")
            else:
                node_obj.props.update(update_props)
                client.update(node_obj)
                console.print(f"[green]Updated properties on {node}[/green]")

    except Exception as ex:
        console.print(f"[bold red]Error: {ex}[/bold red]")
        raise typer.Exit(1) from ex
