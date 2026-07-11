"""CANFAR Session."""

from __future__ import annotations

import asyncio
import re
from typing import TYPE_CHECKING, Any
from webbrowser import open_new_tab

from httpx import HTTPError, Response

from canfar import get_logger
from canfar.client import HTTPClient
from canfar.models.session import CreateRequest
from canfar.utils import build

if TYPE_CHECKING:
    from collections.abc import Mapping

    from canfar.models.types import Kind, Status, View
log = get_logger(__name__)


def _log_http_task_failure(operation: str, context: object, exc: BaseException) -> None:
    """Log a failed HTTP task with safe caller context.

    Status codes and safe request context are already logged by HTTPX response hooks;
    this adds a Session identifier or replica position and exception class only.
    """
    log.error("%s: %s (%s)", operation, context, type(exc).__name__)


def _ids(value: str | list[str]) -> list[str]:
    """Normalize one or many Session identifiers without changing their order."""
    return [value] if isinstance(value, str) else value


def _session_name_pattern(selector: str) -> re.Pattern[str]:
    """Compile a regular expression or an anchored literal Session selector."""
    meta = frozenset(".^$*+?{}[]()|")
    if any(char in meta for char in selector):
        log.info("destroy_with using regex pattern: %s", selector)
        pattern = selector
    else:
        log.info("destroy_with using literal prefix: %s", selector)
        pattern = rf"^{re.escape(selector)}"
    return re.compile(pattern)


def connection_url(session: Mapping[str, Any]) -> str | None:
    """Return the URL only when a Session is ready for a connection."""
    value = session.get("connectURL")
    if session.get("status") != "Running" or not isinstance(value, str):
        return None
    return value or None


class Session(HTTPClient):
    """CANFAR Session Management Client.

    This class provides methods to manage sessions, including fetching
    session details, creating new sessions, retrieving logs, and
    destroying existing sessions. It is a subclass of the `HTTPClient`
    class and inherits its attributes and methods.

    Examples:
        >>> from canfar.sessions import Session
        >>> session = Session(
                timeout=120,
                concurrency=100, # No effect on sync client
            )
    """

    def fetch(
        self,
        kind: Kind | None = None,
        status: Status | None = None,
        view: View | None = None,
    ) -> list[dict[str, str]]:
        """Fetch open sessions for the user.

        Args:
            kind (Kind | None, optional): Session kind. Defaults to None.
            status (Status | None, optional): Session status. Defaults to None.
            view (View | None, optional): View leve. Defaults to None.

        Returns:
            list[dict[str, str]]: Session[s] information.

        Examples:
            >>> from canfar.sessions import Session
            >>> session = Session()
            >>> session.fetch(kind="notebook")
            [{'id': 'ikvp1jtp',
              'userid': 'username',
              'image': 'image-server/image/label:latest',
              'type': 'notebook',
              'status': 'Running',
              'name': 'example-notebook',
              'startTime': '2222-12-14T02:24:06Z',
              'connectURL': 'https://something.example.com/ikvp1jtp',
              'requestedRAM': '16G',
              'requestedCPUCores': '2',
              'requestedGPUCores': '<none>',
              'coresInUse': '0m',
              'ramInUse': '101Mi'}]
        """
        parameters: dict[str, Any] = build.fetch_parameters(kind, status, view)
        response: Response = self.client.get(url="session", params=parameters)
        data: list[dict[str, str]] = response.json()
        return data

    def stats(self) -> dict[str, Any]:
        """Get statistics for the entire platform.

        Returns:
            Dict[str, Any]: Cluster statistics.

        Examples:
            >>> from canfar.sessions import Session
            >>> session = Session()
            >>> session.stats()
            {'cores': {'requestedCPUCores': 377,
             'coresAvailable': 960,
             'maxCores': {'cores': 32, 'withRam': '147Gi'}},
             'ram': {'maxRAM': {'ram': '226Gi', 'withCores': 32}}}
        """
        parameters = {"view": "stats"}
        response: Response = self.client.get("session", params=parameters)
        data: dict[str, Any] = response.json()
        return data

    def info(self, ids: list[str] | str) -> list[dict[str, Any]]:
        """Get information about session[s].

        Args:
            ids (Union[List[str], str]): Session ID[s].

        Returns:
            list[dict[str, Any]]: Session information.

        Examples:
            >>> session.info(ids="hjko98yghj")
            >>> session.info(ids=["hjko98yghj", "ikvp1jtp"])
        """
        ids = _ids(ids)
        results: list[dict[str, Any]] = []
        for value in ids:
            try:
                response: Response = self.client.get(url=f"session/{value}")
                results.append(response.json())
            except HTTPError as err:
                _log_http_task_failure("failed to fetch session info for", value, err)
        return results

    def logs(
        self,
        ids: list[str] | str,
        verbose: bool = False,
    ) -> dict[str, str] | None:
        """Get logs from a session[s].

        Args:
            ids (Union[List[str], str]): Session ID[s].
            verbose (bool, optional): Print logs to stdout. Defaults to False.

        Returns:
            Dict[str, str]: Logs in text/plain format.

        Examples:
            >>> session.logs(ids="hjko98yghj")
            >>> session.logs(ids=["hjko98yghj", "ikvp1jtp"])
        """
        ids = _ids(ids)
        parameters: dict[str, str] = {"view": "logs"}
        results: dict[str, str] = {}

        for value in ids:
            try:
                response: Response = self.client.get(
                    url=f"session/{value}",
                    params=parameters,
                )
                results[value] = response.text
            except HTTPError as err:
                _log_http_task_failure("failed to fetch logs for session", value, err)

        if verbose:
            for key, value in results.items():
                log.info("Session ID: %s\n", key)
                log.info(value)
            return None

        return results

    def create(
        self,
        name: str | CreateRequest,
        image: str | None = None,
        cores: int | None = None,
        ram: int | None = None,
        kind: Kind = "headless",
        gpu: int | None = None,
        cmd: str | None = None,
        args: str | None = None,
        env: dict[str, Any] | None = None,
        replicas: int = 1,
    ) -> list[str]:
        """Launch a canfar session.

        Args:
            name: Domain request or a unique name for the Session.
            image: Container Image when ``name`` is a string.
            cores (int, optional): Number of cores.
                Defaults to None, i.e. flexible mode.
            ram (int, optional): Amount of RAM (GB).
                Defaults to None, i.e. flexible mode.
            kind (str, optional): Type of canfar session. Defaults to "headless".
            gpu (Optional[int], optional): Number of GPUs. Defaults to None.
            cmd (Optional[str], optional): Command to run. Defaults to None.
            args (Optional[str], optional): Arguments to the command. Defaults to None.
            env (Optional[Dict[str, Any]], optional): Environment variables to inject.
                Defaults to None.
            replicas (int, optional): Number of sessions to launch. Defaults to 1.

        Notes:
            - If cores and ram are not specified, the session will be created with
              flexible resource allocation of upto 8 cores and 32GB of RAM.
            - The name of the session suffixed with the replica number. eg. test-42
              when replicas > 1.
            - Each container will have the following environment variables injected:
                * REPLICA_ID - The replica number
                * REPLICA_COUNT - The total number of replicas

        Returns:
            List[str]: Session IDs for launched sessions. On HTTP or network failure
                for a given attempt, that attempt is omitted; if all attempts fail,
                returns an empty list. Does not raise for those errors.

        Examples:
            >>> from canfar.sessions import Session
            >>> session = Session()
            >>> session.create(
                    name="test",
                    image='images.canfar.net/skaha/terminal:1.1.1',
                    cores=2,
                    ram=8,
                    gpu=1,
                    kind="headless",
                    cmd="env",
                    env={"TEST": "test"},
                    replicas=2,
                )
            >>> ["hjko98yghj", "ikvp1jtp"]
        """
        payloads = build.create_parameters(
            name,
            image,
            cores,
            ram,
            kind,
            gpu,
            cmd,
            args,
            env,
            replicas,
        )
        results: list[str] = []
        session_kind = name.kind if isinstance(name, CreateRequest) else kind
        log.debug("Creating %d %s session[s].", len(payloads), session_kind)
        for replica, payload in enumerate(payloads, start=1):
            try:
                response: Response = self.client.post(url="session", params=payload)
                results.append(response.text.rstrip("\r\n"))
            except HTTPError as err:
                _log_http_task_failure(
                    "Failed to create session",
                    f"replica {replica}/{len(payloads)}",
                    err,
                )
        return results

    def events(
        self,
        ids: str | list[str],
        verbose: bool = False,
    ) -> list[dict[str, str]] | None:
        """Get deployment events for a session[s].

        Args:
            ids (Union[str, List[str]]): Session ID[s].
            verbose (bool, optional): Print events to stdout. Defaults to False.

        Returns:
            Optional[List[Dict[str, str]]]: A list of events for the session[s].

        Notes:
            When verbose is True, the events will be printed to stdout only.

        Examples:
            >>> from canfar.sessions import Session
            >>> session = Session()
            >>> session.events(ids="hjko98yghj")
            >>> session.events(ids=["hjko98yghj", "ikvp1jtp"])
        """
        ids = _ids(ids)
        results: list[dict[str, str]] = []
        parameters: dict[str, str] = {"view": "events"}
        for value in ids:
            try:
                response: Response = self.client.get(
                    url=f"session/{value}",
                    params=parameters,
                )
                results.append({value: response.text})
            except HTTPError as err:
                _log_http_task_failure("Failed to fetch events for session", value, err)
        if verbose and results:
            for result in results:
                for key, value in result.items():
                    log.info("Session ID: %s", key)
                    log.info("\n %s", value)
        return results if not verbose else None

    def destroy(self, ids: str | list[str]) -> dict[str, bool]:
        """Destroy canfar session[s].

        Args:
            ids (Union[str, List[str]]): Session ID[s].

        Returns:
            Dict[str, bool]: A dictionary of session IDs
            and a bool indicating if the session was destroyed.

        Examples:
            >>> from canfar.sessions import Session
            >>> session = Session()
            >>> session.destroy(ids="hjko98yghj")
            >>> session.destroy(ids=["hjko98yghj", "ikvp1jtp"])
        """
        ids = _ids(ids)
        results: dict[str, bool] = {}
        for value in ids:
            try:
                self.client.delete(url=f"session/{value}")
                results[value] = True
            except HTTPError:
                msg = f"Failed to destroy session {value}"
                log.exception(msg)
                results[value] = False
        return results

    def destroy_with(
        self,
        prefix: str,
        *,
        kind: Kind = "headless",
        status: Status = "Completed",
    ) -> dict[str, bool]:
        """Destroy session[s] matching a prefix or regex.

        Args:
            prefix (str): Prefix to match.
                Treated literally unless regex meta-characters are found.
            kind (Kind): Type of session. Defaults to "headless".
            status (Status): Status of the session. Defaults to "Completed".

        Returns:
            Dict[str, bool]: A dictionary of session IDs
            and a bool indicating if the session was destroyed.

        Notes:
            - If the value contains regex metacharacters (e.g., `.^$*+?{}[]()|`),
              it is treated as a regex with :func:`re.search`.
            - Otherwise it is treated as a literal prefix (anchored with `^`).
            This method is useful for destroying multiple sessions at once.

        Examples:
            >>> from canfar.sessions import Session
            >>> session = Session()
            >>> session.destroy_with(prefix="test")  # literal prefix
            >>> session.destroy_with(prefix="desktop$")  # regex
        """
        try:
            regex = _session_name_pattern(prefix)
        except re.error as exc:
            msg = f"Invalid regex pattern '{prefix}': {exc}"
            log.exception(msg)
            raise ValueError(msg) from exc

        sessions = self.fetch(kind=kind, status=status)
        ids: list[str] = [
            session["id"] for session in sessions if regex.search(session["name"])
        ]
        return self.destroy(ids)

    def connect(self, ids: list[str] | str) -> None:
        """Open session[s] in a web browser.

        Args:
            ids (Union[List[str], str]): Session ID[s].

        Examples:
            >>> from canfar.sessions import Session
            >>> session = Session()
            >>> session.connect(ids="hjko98yghj")
            >>> session.connect(ids=["hjko98yghj", "ikvp1jtp"])
        """
        info = self.info(_ids(ids))
        log.debug(info)
        for session in info:
            status: str = session.get("status", "unknown")
            url = connection_url(session)
            if url is None and status != "Running":
                log.warning("Session %s is currently %s.", session["id"], status)
                log.warning("Please wait for the session to be ready.")
                continue
            if url is not None:
                open_new_tab(url)


class AsyncSession(HTTPClient):
    """Asynchronous CANFAR Session Management Client.

    This class provides methods to manage sessions in the system,
    including fetching session details, creating new sessions,
    retrieving logs, and destroying existing sessions.

    This class is a subclass of the `HTTPClient` class and inherits its
    attributes and methods.

    Examples:
        >>> from canfar.sessions import AsyncSession
        >>> session = AsyncSession(
                url="https://ws-uv.canfar.net/skaha",
                token="token",
                timeout=30,
                concurrency=100,
            )
    """

    async def fetch(
        self,
        kind: Kind | None = None,
        status: Status | None = None,
        view: View | None = None,
    ) -> list[dict[str, str]]:
        """List open sessions for the user.

        Args:
            kind (Kind | None, optional): Session kind. Defaults to None.
            status (Status | None, optional): Session status. Defaults to None.
            view (View | None, optional): Session view level. Defaults to None.

        Notes:
            By default, only the calling user's sessions are listed. If views is
            set to 'all', all user sessions are listed (with limited information).

        Returns:
            list: Sessions information.

        Examples:
            >>> from canfar.sessions import AsyncSession
            >>> session = AsyncSession()
            >>> await session.fetch(kind="notebook")
            [{'id': 'vl91sfzz',
            'userid': 'brars',
            'runAsUID': '166169204',
            'runAsGID': '166169204',
            'supplementalGroups': [34241,
            34337,
            35124,
            36227,
            1902365706,
            1454823273,
            1025424273],
            'appid': '<none>',
            'image': 'image-server/repo/image:version',
            'type': 'notebook',
            'status': 'Running',
            'name': 'notebook1',
            'startTime': '2025-03-05T21:48:29Z',
            'expiryTime': '2025-03-09T21:48:29Z',
            'connectURL': 'https://canfar.net/session/notebook/some/url',
            'requestedRAM': '8G',
            'requestedCPUCores': '2',
            'requestedGPUCores': '0',
            'ramInUse': '<none>',
            'gpuRAMInUse': '<none>',
            'cpuCoresInUse': '<none>',
            'gpuUtilization': '<none>'}]
        """
        parameters: dict[str, Any] = build.fetch_parameters(kind, status, view)
        response: Response = await self.asynclient.get(url="session", params=parameters)
        data: list[dict[str, str]] = response.json()
        return data

    async def stats(self) -> dict[str, Any]:
        """Get statistics for the canfar cluster.

        Returns:
            Dict[str, Any]: Cluster statistics.

        Examples:
            >>> from canfar.sessions import AsyncSession
            >>> session = AsyncSession()
            >>> await session.stats()
            {'cores': {'requestedCPUCores': 377,
             'coresAvailable': 960,
             'maxCores': {'cores': 32, 'withRam': '147Gi'}},
             'ram': {'maxRAM': {'ram': '226Gi', 'withCores': 32}}}
        """
        parameters = {"view": "stats"}
        response: Response = await self.asynclient.get("session", params=parameters)
        data: dict[str, Any] = response.json()
        return data

    async def info(self, ids: list[str] | str) -> list[dict[str, Any]]:
        """Get information about session[s].

        Args:
            ids (Union[List[str], str]): Session ID[s].

        Returns:
            list[dict[str, Any]]: Session information.

        Examples:
            >>> from canfar.sessions import AsyncSession
            >>> session = AsyncSession()
            >>> await session.info(ids="hjko98yghj")
            >>> await session.info(ids=["hjko98yghj", "ikvp1jtp"])
        """
        ids = _ids(ids)
        results: list[dict[str, Any]] = []
        semaphore: asyncio.Semaphore = asyncio.Semaphore(self.concurrency)

        async def bounded(value: str) -> dict[str, Any]:
            async with semaphore:
                response = await self.asynclient.get(url=f"session/{value}")
                data: dict[str, Any] = response.json()
                return data

        tasks = [bounded(value) for value in ids]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        for value, reply in zip(ids, responses, strict=True):
            if isinstance(reply, Exception):
                _log_http_task_failure("failed to fetch session info for", value, reply)
            elif isinstance(reply, dict):
                results.append(reply)
        log.debug("Session info records collected: %s", results)
        return results

    async def logs(
        self,
        ids: list[str] | str,
        verbose: bool = False,
    ) -> dict[str, str] | None:
        """Get logs from a session[s].

        Args:
            ids (Union[List[str], str]): Session ID[s].
            verbose (bool, optional): Print logs to stdout. Defaults to False.

        Returns:
            Dict[str, str]: Logs in text/plain format.

        Examples:
            >>> from canfar.sessions import AsyncSession
            >>> session = AsyncSession()
            >>> await session.logs(ids="hjko98yghj")
            >>> await session.logs(ids=["hjko98yghj", "ikvp1jtp"])
        """
        ids = _ids(ids)
        parameters: dict[str, str] = {"view": "logs"}
        results: dict[str, str] = {}

        semaphore: asyncio.Semaphore = asyncio.Semaphore(self.concurrency)

        async def bounded(value: str) -> tuple[str, str]:
            async with semaphore:
                response = await self.asynclient.get(
                    url=f"session/{value}",
                    params=parameters,
                )
                return value, response.text

        tasks = [bounded(value) for value in ids]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        for value, reply in zip(ids, responses, strict=True):
            if isinstance(reply, Exception):
                _log_http_task_failure("failed to fetch logs for session", value, reply)
            elif isinstance(reply, tuple):
                results[reply[0]] = reply[1]

        # Print logs to stdout if verbose is set to True
        if verbose:
            for key, value in results.items():
                log.info("Session ID: %s\n", key)
                log.info(value)
            return None
        return results

    async def create(
        self,
        name: str | CreateRequest,
        image: str | None = None,
        cores: int | None = None,
        ram: int | None = None,
        kind: Kind = "headless",
        gpu: int | None = None,
        cmd: str | None = None,
        args: str | None = None,
        env: dict[str, Any] | None = None,
        replicas: int = 1,
    ) -> list[str]:
        """Launch a canfar session.

        Args:
            name: Domain request or a unique name for the Session.
            image: Container Image when ``name`` is a string.
            cores (int, optional): Number of cores.
                Defaults to None, i.e. flexible mode.
            ram (int, optional): Amount of RAM (GB).
                Defaults to None, i.e. flexible mode.
            kind (str, optional): Type of canfar session. Defaults to "headless".
            gpu (Optional[int], optional): Number of GPUs. Defaults to None.
            cmd (Optional[str], optional): Command to run. Defaults to None.
            args (Optional[str], optional): Arguments to the command. Defaults to None.
            env (Optional[Dict[str, Any]], optional): Environment variables to inject.
                Defaults to None.
            replicas (int, optional): Number of sessions to launch. Defaults to 1.

        Notes:
            - If cores and ram are not specified, the session will be created with
              flexible resource allocation of upto 8 cores and 32GB of RAM.
            - The name of the session suffixed with the replica number. eg. test-42
              when replicas > 1.
            - Each container will have the following environment variables injected:
                * REPLICA_ID - The replica number
                * REPLICA_COUNT - The total number of replicas

        Returns:
            List[str]: Session IDs for launched sessions. On HTTP or network failure
                for a given attempt, that attempt is omitted; if all attempts fail,
                returns an empty list. Does not raise for those errors.

        Examples:
            >>> from canfar.sessions import AsyncSession
            >>> session = AsyncSession()
            >>> await session.create(
                    name="test",
                    image='images.canfar.net/skaha/terminal:1.1.1',
                    cores=2,
                    ram=8,
                    gpu=1,
                    kind="headless",
                    cmd="env",
                    env={"TEST": "test"},
                    replicas=2,
                )
            >>> ["hjko98yghj", "ikvp1jtp"]
        """
        payloads: list[list[tuple[str, Any]]] = build.create_parameters(
            name,
            image,
            cores,
            ram,
            kind,
            gpu,
            cmd,
            args,
            env,
            replicas,
        )
        results: list[str] = []
        semaphore: asyncio.Semaphore = asyncio.Semaphore(self.concurrency)

        async def bounded(parameters: list[tuple[str, Any]]) -> Any:
            async with semaphore:
                response = await self.asynclient.post(url="session", params=parameters)
                return response.text.rstrip("\r\n")

        tasks = [bounded(payload) for payload in payloads]
        session_kind = name.kind if isinstance(name, CreateRequest) else kind
        msg = f"Creating {len(payloads)} {session_kind} session[s]."
        log.debug(msg)
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        for replica, reply in enumerate(responses, start=1):
            if isinstance(reply, Exception):
                _log_http_task_failure(
                    "Failed to create session",
                    f"replica {replica}/{len(payloads)}",
                    reply,
                )
            elif isinstance(reply, str):
                results.append(reply)
        log.debug("Session IDs collected from create: %s", results)
        return results

    async def events(
        self,
        ids: str | list[str],
        verbose: bool = False,
    ) -> list[dict[str, str]] | None:
        """Get deployment events for a session[s].

        Args:
            ids (Union[str, List[str]]): Session ID[s].
            verbose (bool, optional): Print events to stdout. Defaults to False.

        Returns:
            Optional[List[Dict[str, str]]]: A list of events for the session[s].

        Notes:
            When verbose is True, the events will be printed to stdout only.

        Examples:
            >>> from canfar.sessions import AsyncSession
            >>> session = AsyncSession()
            >>> await session.events(ids="hjko98yghj")
            >>> await session.events(ids=["hjko98yghj", "ikvp1jtp"])
        """
        ids = _ids(ids)
        results: list[dict[str, str]] = []
        parameters: dict[str, str] = {"view": "events"}
        semaphore: asyncio.Semaphore = asyncio.Semaphore(self.concurrency)

        async def bounded(value: str) -> dict[str, str]:
            async with semaphore:
                response = await self.asynclient.get(
                    url=f"session/{value}",
                    params=parameters,
                )
                return {value: response.text}

        tasks = [bounded(value) for value in ids]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        for value, reply in zip(ids, responses, strict=True):
            if isinstance(reply, Exception):
                _log_http_task_failure(
                    "Failed to fetch events for session",
                    value,
                    reply,
                )
            elif isinstance(reply, dict):
                results.append(reply)

        if verbose and results:
            for result in results:
                for key, value in result.items():
                    log.info("Session ID: %s", key)
                    log.info(value)
        log.debug("Session events collected: %s", results)
        return results if not verbose else None

    async def destroy(self, ids: str | list[str]) -> dict[str, bool]:
        """Destroy session[s].

        Args:
            ids (Union[str, List[str]]): Session ID[s].

        Returns:
            Dict[str, bool]: A dictionary of session IDs
            and a bool indicating if the session was destroyed.

        Examples:
            >>> from canfar.sessions import AsyncSession
            >>> session = AsyncSession()
            >>> await session.destroy(ids="hjko98yghj")
            >>> await session.destroy(ids=["hjko98yghj", "ikvp1jtp"])
        """
        ids = _ids(ids)
        results: dict[str, bool] = {}
        semaphore: asyncio.Semaphore = asyncio.Semaphore(self.concurrency)

        async def bounded(value: str) -> tuple[str, bool]:
            async with semaphore:
                try:
                    await self.asynclient.delete(url=f"session/{value}")
                except HTTPError as err:
                    msg = f"Failed to destroy session {value}: {err}"
                    log.exception(msg)
                    return value, False
                else:
                    return value, True

        tasks = [bounded(value) for value in ids]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        for reply in responses:
            if isinstance(reply, tuple):
                results[reply[0]] = reply[1]
        log.debug(results)
        return results

    async def destroy_with(
        self,
        prefix: str,
        kind: Kind = "headless",
        status: Status = "Completed",
    ) -> dict[str, bool]:
        """Destroy session[s] matching a prefix or regex pattern.

        Args:
            prefix (str): Prefix to match.
                Treated literally unless regex meta-characters are found.
            kind (Kind): Type of session. Defaults to "headless".
            status (Status): Status of the session. Defaults to "Completed".


        Returns:
            Dict[str, bool]: A dictionary of session IDs
            and a bool indicating if the session was destroyed.

        Notes:
            - If the value contains regex metacharacters (e.g., `.^$*+?{}[]()|`), it is
                treated as a regex with :func:`re.search`.
            - Otherwise it is treated as a literal prefix (anchored with `^`).
            This method is useful for destroying multiple sessions at once.

        Examples:
            >>> from canfar.sessions import AsyncSession
            >>> session = AsyncSession()
            >>> await session.destroy_with(prefix="test")  # literal prefix
            >>> await session.destroy_with(prefix="desktop$")  # regex
        """
        try:
            regex = _session_name_pattern(prefix)
        except re.error as err:
            msg = f"Invalid regex pattern '{prefix}': {err}"
            log.exception(msg)
            raise ValueError(msg) from err

        ids: list[str] = [
            session["id"]
            for session in await self.fetch(kind=kind, status=status)
            if regex.search(session["name"])
        ]
        return await self.destroy(ids)

    async def connect(self, ids: list[str] | str) -> None:
        """Connect to a session[s] in a web browser.

        Args:
            ids (Union[List[str], str]): Session ID[s].

        Examples:
            >>> from canfar.sessions import AsyncSession
            >>> session = AsyncSession()
            >>> await session.connect(ids="hjko98yghj")
            >>> await session.connect(ids=["hjko98yghj", "ikvp1jtp"])
        """
        info = await self.info(_ids(ids))
        log.debug(info)
        for session in info:
            status: str = session.get("status", "unknown")
            url = connection_url(session)
            if url is None and status != "Running":
                log.warning("Session %s is currently %s.", session["id"], status)
                log.warning("Please wait for the session to be ready.")
                continue
            if url is not None:
                open_new_tab(url)
