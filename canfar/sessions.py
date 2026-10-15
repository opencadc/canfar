"""CANFAR Session."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Literal
from webbrowser import open_new_tab

from httpx2 import HTTPError, Response
from pydantic import Field

from canfar.client import HTTPClient
from canfar.helpers.session import (
    _destroy_failure,
    _ids,
    _matching_session_ids,
    _raise_authentication_failure,
    _raise_failures,
    _renew,
    _response_session_id,
    _session_name_pattern,
    _session_url,
    _task_result,
    connection_url,
)
from canfar.models.session import CreateRequest
from canfar.utils import build

if TYPE_CHECKING:
    from canfar.models.types import Kind, Status
log = logging.getLogger(__name__)

_ERRORS_DESCRIPTION = (
    "'ignore' returns partial results and logs failures; 'raise' raises "
    "SessionRequestError after every request has run."
)


class Session(HTTPClient):
    """CANFAR Session Management Client.

    This class provides methods to manage sessions, including fetching
    session details, creating new sessions, retrieving logs, renewing and
    destroying existing sessions. It is a subclass of the `HTTPClient`
    class and inherits its attributes and methods.

    Examples:
        >>> from canfar.sessions import Session
        >>> session = Session(
                timeout=120,
                concurrency=100, # No effect on sync client
            )
    """

    errors: Literal["ignore", "raise"] = Field(
        "ignore", title="Error Policy", description=_ERRORS_DESCRIPTION
    )

    def fetch(
        self,
        kind: Kind | None = None,
        status: Status | None = None,
    ) -> list[dict[str, str]]:
        """Fetch open sessions for the user.

        Args:
            kind (Kind | None, optional): Session kind. Defaults to None.
            status (Status | None, optional): Session status. Defaults to None.

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
        parameters: dict[str, Any] = build.fetch_parameters(kind, status)
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

    def info(
        self,
        ids: list[str] | str,
        *,
        errors: Literal["ignore", "raise"] | None = None,
    ) -> list[dict[str, Any]]:
        """Get information about session[s].

        Args:
            ids (Union[List[str], str]): Session ID[s].
            errors: Failure policy for this call. Defaults to the client's
                ``errors`` setting.

        Returns:
            list[dict[str, Any]]: Session information.

        Raises:
            SessionRequestError: If ``errors`` is ``"raise"`` and any request failed.

        Examples:
            >>> session.info(ids="hjko98yghj")
            >>> session.info(ids=["hjko98yghj", "ikvp1jtp"])
        """
        ids = _ids(ids)
        results: list[dict[str, Any]] = []
        failures: dict[str | int, HTTPError] = {}
        for value in ids:
            try:
                response: Response = self.client.get(url=_session_url(value))
                results.append(response.json())
            except HTTPError as err:
                failures[value] = err
                _task_result("failed to fetch session info for", value, err)
        _raise_failures("info", errors or self.errors, results, failures)
        return results

    def logs(
        self,
        ids: list[str] | str,
        verbose: bool = False,
        *,
        errors: Literal["ignore", "raise"] | None = None,
    ) -> dict[str, str] | None:
        """Get logs from a session[s].

        Args:
            ids (Union[List[str], str]): Session ID[s].
            verbose: Send logs to the ``canfar.sessions`` logger and return None.
                Defaults to False, which returns the collected logs.
            errors: Failure policy for this call. Defaults to the client's
                ``errors`` setting.

        Returns:
            Dict[str, str]: Logs in text/plain format.

        Raises:
            SessionRequestError: If ``errors`` is ``"raise"`` and any request failed.

        Examples:
            >>> session.logs(ids="hjko98yghj")
            >>> session.logs(ids=["hjko98yghj", "ikvp1jtp"])
        """
        ids = _ids(ids)
        parameters: dict[str, str] = {"view": "logs"}
        results: dict[str, str] = {}
        failures: dict[str | int, HTTPError] = {}

        for value in ids:
            try:
                response: Response = self.client.get(
                    url=_session_url(value),
                    params=parameters,
                )
                results[value] = response.text
            except HTTPError as err:
                failures[value] = err
                _task_result("failed to fetch logs for session", value, err)

        if verbose:
            for key, value in results.items():
                log.info("Session ID: %s\n", key)
                log.info(value)
        output = None if verbose else results
        _raise_failures("logs", errors or self.errors, output, failures)
        return output

    def create(  # noqa: PLR0917
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
        *,
        errors: Literal["ignore", "raise"] | None = None,
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
            errors: Failure policy for this call. Defaults to the client's
                ``errors`` setting.

        Notes:
            - If cores and ram are not specified, the Session uses the Server's
              flexible resource allocation policy. Limits depend on the Server.
            - The name of the session suffixed with the replica number. eg. test-42
              when replicas > 1.
            - Each container will have the following environment variables injected:
                * REPLICA_ID - The replica number
                * REPLICA_COUNT - The total number of replicas

        Returns:
            List[str]: Session IDs for launched sessions. With ``errors="ignore"``,
                an attempt that fails with an HTTP or network error is omitted; if
                all attempts fail, returns an empty list.

        Raises:
            SessionRequestError: If ``errors`` is ``"raise"`` and any replica failed.
                Its ``errors`` are keyed by 1-based replica number.

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
        failures: dict[str | int, HTTPError] = {}
        session_kind = name.kind if isinstance(name, CreateRequest) else kind
        log.debug("Creating %d %s session[s].", len(payloads), session_kind)
        for replica, payload in enumerate(payloads, start=1):
            try:
                response: Response = self.client.post(url="session", params=payload)
                results.append(_response_session_id(response))
            except HTTPError as err:
                failures[replica] = err
                _task_result(
                    "Failed to create session",
                    f"replica {replica}/{len(payloads)}",
                    err,
                )
        _raise_failures("create", errors or self.errors, results, failures)
        return results

    def events(
        self,
        ids: str | list[str],
        verbose: bool = False,
        *,
        errors: Literal["ignore", "raise"] | None = None,
    ) -> list[dict[str, str]] | None:
        """Get deployment events for a session[s].

        Args:
            ids (Union[str, List[str]]): Session ID[s].
            verbose: Send events to the ``canfar.sessions`` logger and return None.
                Defaults to False, which returns the collected events.
            errors: Failure policy for this call. Defaults to the client's
                ``errors`` setting.

        Returns:
            Optional[List[Dict[str, str]]]: A list of events for the session[s].

        Raises:
            SessionRequestError: If ``errors`` is ``"raise"`` and any request failed.

        Notes:
            Configure application logging to display verbose events. Their output
            follows the configured handlers, rather than printing to stdout.

        Examples:
            >>> from canfar.sessions import Session
            >>> session = Session()
            >>> session.events(ids="hjko98yghj")
            >>> session.events(ids=["hjko98yghj", "ikvp1jtp"])
        """
        ids = _ids(ids)
        results: list[dict[str, str]] = []
        failures: dict[str | int, HTTPError] = {}
        parameters: dict[str, str] = {"view": "events"}
        for value in ids:
            try:
                response: Response = self.client.get(
                    url=_session_url(value),
                    params=parameters,
                )
                results.append({value: response.text})
            except HTTPError as err:
                failures[value] = err
                _task_result("Failed to fetch events for session", value, err)
        if verbose and results:
            for result in results:
                for key, value in result.items():
                    log.info("Session ID: %s", key)
                    log.info("\n %s", value)
        output = results if not verbose else None
        _raise_failures("events", errors or self.errors, output, failures)
        return output

    def destroy(
        self,
        ids: str | list[str],
        *,
        errors: Literal["ignore", "raise"] | None = None,
    ) -> dict[str, bool]:
        """Destroy canfar session[s].

        Args:
            ids (Union[str, List[str]]): Session ID[s].
            errors: Failure policy for this call. Defaults to the client's
                ``errors`` setting.

        Returns:
            Dict[str, bool]: A dictionary of session IDs
            and a bool indicating if the session was destroyed.

        Raises:
            SessionRequestError: If ``errors`` is ``"raise"`` and any request failed.

        Examples:
            >>> from canfar.sessions import Session
            >>> session = Session()
            >>> session.destroy(ids="hjko98yghj")
            >>> session.destroy(ids=["hjko98yghj", "ikvp1jtp"])
        """
        ids = _ids(ids)
        results: dict[str, bool] = {}
        failures: dict[str | int, HTTPError] = {}
        for value in ids:
            try:
                self.client.delete(url=_session_url(value))
                results[value] = True
            except HTTPError as err:
                failures[value] = err
                results[value] = _destroy_failure(value)
        _raise_failures("destroy", errors or self.errors, results, failures)
        return results

    def renew(
        self,
        ids: str | list[str],
        *,
        errors: Literal["ignore", "raise"] | None = None,
    ) -> dict[str, bool]:
        """Renew interactive session[s], resetting their lifetime.

        Args:
            ids (Union[str, List[str]]): Session ID[s].
            errors: Failure policy for this call. Defaults to the client's
                ``errors`` setting.

        Returns:
            Dict[str, bool]: A dictionary of session IDs
            and a bool indicating if the session was renewed.

        Raises:
            SessionRequestError: If ``errors`` is ``"raise"`` and any request failed.

        Examples:
            >>> from canfar.sessions import Session
            >>> session = Session()
            >>> session.renew(ids="hjko98yghj")
            >>> session.renew(ids=["hjko98yghj", "ikvp1jtp"])
        """
        ids = _ids(ids)
        results: dict[str, bool] = {}
        failures: dict[str | int, HTTPError] = {}
        for value in ids:
            try:
                self.client.post(url=_session_url(value), params={"action": "renew"})
                results[value] = True
            except HTTPError as err:
                failures[value] = err
                results[value] = _renew(value)
        _raise_failures("renew", errors or self.errors, results, failures)
        return results

    def destroy_with(
        self,
        prefix: str,
        *,
        kind: Kind = "headless",
        status: Status = "Completed",
        errors: Literal["ignore", "raise"] | None = None,
    ) -> dict[str, bool]:
        """Destroy session[s] matching a prefix or regex.

        Args:
            prefix (str): Prefix to match.
                Treated literally unless regex meta-characters are found.
            kind (Kind): Type of session. Defaults to "headless".
            status (Status): Status of the session. Defaults to "Completed".
            errors: Failure policy for the deletions. Defaults to the client's
                ``errors`` setting.

        Returns:
            Dict[str, bool]: A dictionary of session IDs
            and a bool indicating if the session was destroyed.

        Raises:
            SessionRequestError: If ``errors`` is ``"raise"`` and any deletion failed.

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
        regex = _session_name_pattern(prefix)
        sessions = self.fetch(kind=kind, status=status)
        return self.destroy(_matching_session_ids(sessions, regex), errors=errors)

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
    retrieving logs, renewing and destroying existing sessions.

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

    errors: Literal["ignore", "raise"] = Field(
        "ignore", title="Error Policy", description=_ERRORS_DESCRIPTION
    )

    async def fetch(
        self,
        kind: Kind | None = None,
        status: Status | None = None,
    ) -> list[dict[str, str]]:
        """List open sessions for the user.

        Args:
            kind (Kind | None, optional): Session kind. Defaults to None.
            status (Status | None, optional): Session status. Defaults to None.

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
        parameters: dict[str, Any] = build.fetch_parameters(kind, status)
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

    async def info(
        self,
        ids: list[str] | str,
        *,
        errors: Literal["ignore", "raise"] | None = None,
    ) -> list[dict[str, Any]]:
        """Get information about session[s].

        Args:
            ids (Union[List[str], str]): Session ID[s].
            errors: Failure policy for this call. Defaults to the client's
                ``errors`` setting.

        Returns:
            list[dict[str, Any]]: Session information.

        Raises:
            SessionRequestError: If ``errors`` is ``"raise"`` and any request failed.

        Examples:
            >>> from canfar.sessions import AsyncSession
            >>> session = AsyncSession()
            >>> await session.info(ids="hjko98yghj")
            >>> await session.info(ids=["hjko98yghj", "ikvp1jtp"])
        """
        ids = _ids(ids)
        results: list[dict[str, Any]] = []
        failures: dict[str | int, HTTPError] = {}

        async def request(value: str) -> dict[str, Any]:
            response = await self.asynclient.get(url=_session_url(value))
            data: dict[str, Any] = response.json()
            return data

        tasks = [request(value) for value in ids]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        for value, reply in zip(ids, responses, strict=True):
            if isinstance(reply, HTTPError):
                failures[value] = reply
            result = _task_result("failed to fetch session info for", value, reply)
            if isinstance(result, dict):
                results.append(result)
        log.debug("Session info records collected: %s", results)
        _raise_failures("info", errors or self.errors, results, failures)
        return results

    async def logs(
        self,
        ids: list[str] | str,
        verbose: bool = False,
        *,
        errors: Literal["ignore", "raise"] | None = None,
    ) -> dict[str, str] | None:
        """Get logs from a session[s].

        Args:
            ids (Union[List[str], str]): Session ID[s].
            verbose: Send logs to the ``canfar.sessions`` logger and return None.
                Defaults to False, which returns the collected logs.
            errors: Failure policy for this call. Defaults to the client's
                ``errors`` setting.

        Returns:
            Dict[str, str]: Logs in text/plain format.

        Raises:
            SessionRequestError: If ``errors`` is ``"raise"`` and any request failed.

        Examples:
            >>> from canfar.sessions import AsyncSession
            >>> session = AsyncSession()
            >>> await session.logs(ids="hjko98yghj")
            >>> await session.logs(ids=["hjko98yghj", "ikvp1jtp"])
        """
        ids = _ids(ids)
        parameters: dict[str, str] = {"view": "logs"}
        results: dict[str, str] = {}
        failures: dict[str | int, HTTPError] = {}

        async def request(value: str) -> tuple[str, str]:
            response = await self.asynclient.get(
                url=_session_url(value),
                params=parameters,
            )
            return value, response.text

        tasks = [request(value) for value in ids]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        for value, reply in zip(ids, responses, strict=True):
            if isinstance(reply, HTTPError):
                failures[value] = reply
            result = _task_result("failed to fetch logs for session", value, reply)
            if isinstance(result, tuple):
                results[result[0]] = result[1]

        if verbose:
            for key, value in results.items():
                log.info("Session ID: %s\n", key)
                log.info(value)
        output = None if verbose else results
        _raise_failures("logs", errors or self.errors, output, failures)
        return output

    async def create(  # noqa: PLR0917
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
        *,
        errors: Literal["ignore", "raise"] | None = None,
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
            errors: Failure policy for this call. Defaults to the client's
                ``errors`` setting.

        Notes:
            - If cores and ram are not specified, the Session uses the Server's
              flexible resource allocation policy. Limits depend on the Server.
            - The name of the session suffixed with the replica number. eg. test-42
              when replicas > 1.
            - Each container will have the following environment variables injected:
                * REPLICA_ID - The replica number
                * REPLICA_COUNT - The total number of replicas

        Returns:
            List[str]: Session IDs for launched sessions. With ``errors="ignore"``,
                an attempt that fails with an HTTP or network error is omitted; if
                all attempts fail, returns an empty list.

        Raises:
            SessionRequestError: If ``errors`` is ``"raise"`` and any replica failed.
                Its ``errors`` are keyed by 1-based replica number.

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
        failures: dict[str | int, HTTPError] = {}

        async def request_session(parameters: list[tuple[str, Any]]) -> str:
            response = await self.asynclient.post(url="session", params=parameters)
            return _response_session_id(response)

        tasks = [request_session(payload) for payload in payloads]
        session_kind = name.kind if isinstance(name, CreateRequest) else kind
        msg = f"Creating {len(payloads)} {session_kind} session[s]."
        log.debug(msg)
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        for replica, reply in enumerate(responses, start=1):
            if isinstance(reply, HTTPError):
                failures[replica] = reply
            result = _task_result(
                "Failed to create session",
                f"replica {replica}/{len(payloads)}",
                reply,
            )
            if isinstance(result, str):
                results.append(result)
        log.debug("Session IDs collected from create: %s", results)
        _raise_failures("create", errors or self.errors, results, failures)
        return results

    async def events(
        self,
        ids: str | list[str],
        verbose: bool = False,
        *,
        errors: Literal["ignore", "raise"] | None = None,
    ) -> list[dict[str, str]] | None:
        """Get deployment events for a session[s].

        Args:
            ids (Union[str, List[str]]): Session ID[s].
            verbose: Send events to the ``canfar.sessions`` logger and return None.
                Defaults to False, which returns the collected events.
            errors: Failure policy for this call. Defaults to the client's
                ``errors`` setting.

        Returns:
            Optional[List[Dict[str, str]]]: A list of events for the session[s].

        Raises:
            SessionRequestError: If ``errors`` is ``"raise"`` and any request failed.

        Notes:
            Configure application logging to display verbose events. Their output
            follows the configured handlers, rather than printing to stdout.

        Examples:
            >>> from canfar.sessions import AsyncSession
            >>> session = AsyncSession()
            >>> await session.events(ids="hjko98yghj")
            >>> await session.events(ids=["hjko98yghj", "ikvp1jtp"])
        """
        ids = _ids(ids)
        results: list[dict[str, str]] = []
        failures: dict[str | int, HTTPError] = {}
        parameters: dict[str, str] = {"view": "events"}

        async def request(value: str) -> dict[str, str]:
            response = await self.asynclient.get(
                url=_session_url(value),
                params=parameters,
            )
            return {value: response.text}

        tasks = [request(value) for value in ids]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        for value, reply in zip(ids, responses, strict=True):
            if isinstance(reply, HTTPError):
                failures[value] = reply
            result = _task_result(
                "Failed to fetch events for session",
                value,
                reply,
            )
            if isinstance(result, dict):
                results.append(result)

        if verbose and results:
            for result in results:
                for key, value in result.items():
                    log.info("Session ID: %s", key)
                    log.info(value)
        log.debug("Session events collected: %s", results)
        output = results if not verbose else None
        _raise_failures("events", errors or self.errors, output, failures)
        return output

    async def destroy(
        self,
        ids: str | list[str],
        *,
        errors: Literal["ignore", "raise"] | None = None,
    ) -> dict[str, bool]:
        """Destroy session[s].

        Args:
            ids (Union[str, List[str]]): Session ID[s].
            errors: Failure policy for this call. Defaults to the client's
                ``errors`` setting.

        Returns:
            Dict[str, bool]: A dictionary of session IDs
            and a bool indicating if the session was destroyed.

        Raises:
            SessionRequestError: If ``errors`` is ``"raise"`` and any request failed.

        Examples:
            >>> from canfar.sessions import AsyncSession
            >>> session = AsyncSession()
            >>> await session.destroy(ids="hjko98yghj")
            >>> await session.destroy(ids=["hjko98yghj", "ikvp1jtp"])
        """
        ids = _ids(ids)
        results: dict[str, bool] = {}
        failures: dict[str | int, HTTPError] = {}

        async def request(value: str) -> tuple[str, HTTPError | None]:
            try:
                await self.asynclient.delete(url=_session_url(value))
            except HTTPError as err:
                _destroy_failure(value, err)
                return value, err
            return value, None

        tasks = [request(value) for value in ids]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        for reply in responses:
            _raise_authentication_failure(reply)
            if isinstance(reply, tuple):
                value, failure = reply
                results[value] = failure is None
                if failure is not None:
                    failures[value] = failure
        log.debug(results)
        _raise_failures("destroy", errors or self.errors, results, failures)
        return results

    async def renew(
        self,
        ids: str | list[str],
        *,
        errors: Literal["ignore", "raise"] | None = None,
    ) -> dict[str, bool]:
        """Renew interactive session[s], resetting their lifetime.

        Args:
            ids (Union[str, List[str]]): Session ID[s].
            errors: Failure policy for this call. Defaults to the client's
                ``errors`` setting.

        Returns:
            Dict[str, bool]: A dictionary of session IDs
            and a bool indicating if the session was renewed.

        Raises:
            SessionRequestError: If ``errors`` is ``"raise"`` and any request failed.

        Examples:
            >>> from canfar.sessions import AsyncSession
            >>> session = AsyncSession()
            >>> await session.renew(ids="hjko98yghj")
            >>> await session.renew(ids=["hjko98yghj", "ikvp1jtp"])
        """
        ids = _ids(ids)
        results: dict[str, bool] = {}
        failures: dict[str | int, HTTPError] = {}

        async def request(value: str) -> tuple[str, HTTPError | None]:
            try:
                await self.asynclient.post(
                    url=_session_url(value), params={"action": "renew"}
                )
            except HTTPError as err:
                _renew(value, err)
                return value, err
            return value, None

        tasks = [request(value) for value in ids]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        for reply in responses:
            _raise_authentication_failure(reply)
            if isinstance(reply, tuple):
                value, failure = reply
                results[value] = failure is None
                if failure is not None:
                    failures[value] = failure
        log.debug(results)
        _raise_failures("renew", errors or self.errors, results, failures)
        return results

    async def destroy_with(
        self,
        prefix: str,
        *,
        kind: Kind = "headless",
        status: Status = "Completed",
        errors: Literal["ignore", "raise"] | None = None,
    ) -> dict[str, bool]:
        """Destroy session[s] matching a prefix or regex pattern.

        Args:
            prefix (str): Prefix to match.
                Treated literally unless regex meta-characters are found.
            kind (Kind): Type of session. Defaults to "headless".
            status (Status): Status of the session. Defaults to "Completed".
            errors: Failure policy for the deletions. Defaults to the client's
                ``errors`` setting.


        Returns:
            Dict[str, bool]: A dictionary of session IDs
            and a bool indicating if the session was destroyed.

        Raises:
            SessionRequestError: If ``errors`` is ``"raise"`` and any deletion failed.

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
        regex = _session_name_pattern(prefix)
        sessions = await self.fetch(kind=kind, status=status)
        return await self.destroy(_matching_session_ids(sessions, regex), errors=errors)

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
