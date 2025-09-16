"""CANFAR Session."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any
from webbrowser import open_new_tab

from httpx import HTTPError, Response

from canfar import get_logger
from canfar.client import HTTPClient
from canfar.utils import build

if TYPE_CHECKING:
    from canfar.models.types import Kind, Status, View
log = get_logger(__name__)


class Session(HTTPClient):
    """CANFAR Session Management Client.

    This class provides methods to manage sessions, including fetching
    session details, creating new sessions, retrieving logs, and
    destroying existing sessions. It is a subclass of the `HTTPClient`
    class and inherits its attributes and methods.

    Examples:
        >>> from canfar.session import Session
        >>> session = Session(
                timeout=120,
                concurrency=100, # No effect on sync client
                loglevel=40,
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
            >>> from canfar.session import Session
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
            >>> from canfar.session import Session
            >>> session = Session()
            >>> session.stats()
            {'instances': {
             'session': 88, 'desktopApp': 30, 'headless': 0, 'total': 118},
             'cores': {'requestedCPUCores': 377,
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
            Dict[str, Any]: Session information.

        Examples:
            >>> session.info(session_id="hjko98yghj")
            >>> session.info(id=["hjko98yghj", "ikvp1jtp"])
        """
        # Convert id to list if it is a string
        if isinstance(ids, str):
            ids = [ids]
        results: list[dict[str, Any]] = []
        for value in ids:
            try:
                response: Response = self.client.get(url=f"session/{value}")
                results.append(response.json())
            except HTTPError:
                err = f"failed to fetch session info for {value}"
                log.exception(err)
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
            >>> session.logs(id="hjko98yghj")
            >>> session.logs(id=["hjko98yghj", "ikvp1jtp"])
        """
        if isinstance(ids, str):
            ids = [ids]
        parameters: dict[str, str] = {"view": "logs"}
        results: dict[str, str] = {}

        for value in ids:
            try:
                response: Response = self.client.get(
                    url=f"session/{value}",
                    params=parameters,
                )
                results[value] = response.text
            except HTTPError:
                err = f"failed to fetch logs for session {value}"
                log.exception(err)

        if verbose:
            for key, value in results.items():
                log.info("Session ID: %s\n", key)
                log.info(value)
            return None

        return results

    def create(
        self,
        name: str,
        image: str,
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
            name (str): A unique name for the session.
            image (str): Container image to use for the session.
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
            List[str]: A list of session IDs for the launched sessions.

        Examples:
            >>> from canfar.session import Session
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
        log.debug("Creating %d %s session[s].", replicas, kind)
        for payload in payloads:
            try:
                response: Response = self.client.post(url="session", params=payload)
                results.append(response.text.rstrip("\r\n"))
            except HTTPError:
                err = f"Failed to create session with payload: {payload}"
                log.exception(err)
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
            >>> from canfar.session import Session
            >>> session = Session()
            >>> session.events(ids="hjko98yghj")
            >>> session.events(ids=["hjko98yghj", "ikvp1jtp"])
        """
        if isinstance(ids, str):
            ids = [ids]
        results: list[dict[str, str]] = []
        parameters: dict[str, str] = {"view": "events"}
        for value in ids:
            try:
                response: Response = self.client.get(
                    url=f"session/{value}",
                    params=parameters,
                )
                results.append({value: response.text})
            except HTTPError:
                err = f"Failed to fetch events for session {value}"
                log.exception(err)
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
            >>> from canfar.session import Session
            >>> session = Session()
            >>> session.destroy(id="hjko98yghj")
            >>> session.destroy(id=["hjko98yghj", "ikvp1jtp"])
        """
        if isinstance(ids, str):
            ids = [ids]
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
        kind: Kind = "headless",
        status: Status = "Completed",
    ) -> dict[str, bool]:
        """Destroy session[s] matching search criteria.

        Args:
            prefix (str): Prefix to match in the session name.
            kind (Kind): Type of session. Defaults to "headless".
            status (Status): Status of the session. Defaults to "Completed".


        Returns:
            Dict[str, bool]: A dictionary of session IDs
            and a bool indicating if the session was destroyed.

        Notes:
            The prefix is case-sensitive.
            This method is useful for destroying multiple sessions at once.

        Examples:
            >>> from canfar.session import Session
            >>> session = Session()
            >>> session.destroy_with(prefix="test")
            >>> session.destroy_with(prefix="test", kind="desktop")
            >>> session.destroy_with(prefix="test", kind="headless", status="Running")

        """
        sessions = self.fetch(kind=kind, status=status)
        ids: list[str] = [
            session["id"] for session in sessions if session["name"].startswith(prefix)
        ]
        return self.destroy(ids)

    def connect(self, ids: list[str] | str) -> None:
        """Open session[s] in a web browser.

        Args:
            ids (Union[List[str], str]): Session ID[s].

        Examples:
            >>> from canfar.session import Session
            >>> session = Session()
            >>> session.browse(id="hjko98yghj")
            >>> session.browse(id=["hjko98yghj", "ikvp1jtp"])
        """
        if isinstance(ids, str):
            ids = [ids]
        for value in ids:
            info = self.info(value)
            connect_url = info[0]["connectURL"]
            open_new_tab(connect_url)


class AsyncSession(HTTPClient):
    """Asynchronous CANFAR Session Management Client.

    This class provides methods to manage sessions in the system,
    including fetching session details, creating new sessions,
    retrieving logs, and destroying existing sessions.

    This class is a subclass of the `HTTPClient` class and inherits its
    attributes and methods.

    Examples:
        >>> from canfar.session import AsyncSession
        >>> session = AsyncSession(
                server="https://something.example.com",
                version="v1",
                token="token",
                timeout=30,
                concurrency=100,
                loglevel=40,
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
            >>> from canfar.session import AsyncSession
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
        log.debug(data)
        return data

    async def stats(self) -> dict[str, Any]:
        """Get statistics for the canfar cluster.

        Returns:
            Dict[str, Any]: Cluster statistics.

        Examples:
            >>> from canfar.session import AsyncSession
            >>> session = AsyncSession()
            >>> await session.stats()
            {'instances': {
             'session': 88, 'desktopApp': 30, 'headless': 0, 'total': 118},
             'cores': {'requestedCPUCores': 377,
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
            Dict[str, Any]: Session information.

        Examples:
            >>> from canfar.session import AsyncSession
            >>> session = AsyncSession()
            >>> await session.info(session_id="hjko98yghj")
            >>> await session.info(id=["hjko98yghj", "ikvp1jtp"])
        """
        # Convert id to list if it is a string
        if isinstance(ids, str):
            ids = [ids]
        results: list[dict[str, Any]] = []
        tasks: list[Any] = []
        semaphore: asyncio.Semaphore = asyncio.Semaphore(self.concurrency)

        async def bounded(value: str) -> dict[str, Any]:
            async with semaphore:
                response = await self.asynclient.get(url=f"session/{value}")
                data: dict[str, Any] = response.json()
                return data

        tasks = [bounded(value) for value in ids]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        for reply in responses:
            if isinstance(reply, Exception):
                log.error(reply)
            elif isinstance(reply, dict):
                results.append(reply)
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
            >>> from canfar.session import AsyncSession
            >>> session = AsyncSession()
            >>> await session.logs(id="hjko98yghj")
            >>> await session.logs(id=["hjko98yghj", "ikvp1jtp"])
        """
        if isinstance(ids, str):
            ids = [ids]
        parameters: dict[str, str] = {"view": "logs"}
        results: dict[str, str] = {}

        semaphore: asyncio.Semaphore = asyncio.Semaphore(self.concurrency)
        tasks: list[Any] = []

        async def bounded(value: str) -> tuple[str, str]:
            async with semaphore:
                response = await self.asynclient.get(
                    url=f"session/{value}",
                    params=parameters,
                )
                return value, response.text

        tasks = [bounded(value) for value in ids]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        for reply in responses:
            if isinstance(reply, Exception):
                log.error(reply)
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
        name: str,
        image: str,
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
            name (str): A unique name for the session.
            image (str): Container image to use for the session.
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
            List[str]: A list of session IDs for the launched sessions.

        Examples:
            >>> from canfar.session import AsyncSession
            >>> session = AsyncSession()
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
        tasks: list[Any] = []
        semaphore: asyncio.Semaphore = asyncio.Semaphore(self.concurrency)

        async def bounded(parameters: list[tuple[str, Any]]) -> Any:
            async with semaphore:
                log.debug("HTTP Request Parameters: %s", parameters)
                response = await self.asynclient.post(url="session", params=parameters)
                return response.text.rstrip("\r\n")

        tasks = [bounded(payload) for payload in payloads]
        msg = f"Creating {replicas} {kind} session[s]."
        log.debug(msg)
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        for reply in responses:
            if isinstance(reply, Exception):
                log.error(reply)
            elif isinstance(reply, str):
                results.append(reply)
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
            >>> from canfar.session import AsyncSession
            >>> session = AsyncSession()
            >>> await session.events(id="hjko98yghj")
            >>> await session.events(id=["hjko98yghj", "ikvp1jtp"])
        """
        if isinstance(ids, str):
            ids = [ids]
        results: list[dict[str, str]] = []
        parameters: dict[str, str] = {"view": "events"}
        tasks: list[Any] = []
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
        for reply in responses:
            if isinstance(reply, Exception):
                log.error(reply)
            elif isinstance(reply, dict):
                results.append(dict(reply))

        if verbose and results:
            for result in results:
                for key, value in result.items():
                    log.info("Session ID: %s", key)
                    log.info(value)
        return results if not verbose else None

    async def destroy(self, ids: str | list[str]) -> dict[str, bool]:
        """Destroy session[s].

        Args:
            ids (Union[str, List[str]]): Session ID[s].

        Returns:
            Dict[str, bool]: A dictionary of session IDs
            and a bool indicating if the session was destroyed.

        Examples:
            >>> from canfar.session import AsyncSession
            >>> session = AsyncSession()
            >>> await session.destroy(id="hjko98yghj")
            >>> await session.destroy(id=["hjko98yghj", "ikvp1jtp"])
        """
        if isinstance(ids, str):
            ids = [ids]
        results: dict[str, bool] = {}
        semaphore: asyncio.Semaphore = asyncio.Semaphore(self.concurrency)
        tasks: list[Any] = []

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
        return results

    async def destroy_with(
        self,
        prefix: str,
        kind: Kind = "headless",
        status: Status = "Completed",
    ) -> dict[str, bool]:
        """Destroy session[s] matching search criteria.

        Args:
            prefix (str): Prefix to match in the session name.
            kind (Kind): Type of session. Defaults to "headless".
            status (Status): Status of the session. Defaults to "Completed".


        Returns:
            Dict[str, bool]: A dictionary of session IDs
            and a bool indicating if the session was destroyed.

        Notes:
            The prefix is case-sensitive.
            This method is useful for destroying multiple sessions at once.

        Examples:
            >>> from canfar.session import AsyncSession
            >>> session = AsyncSession()
            >>> await session.destroy_with(prefix="test")
            >>> await session.destroy_with(prefix="test", kind="desktop")
            >>> await session.destroy_with(prefix="car", kind="carta", status="Running")

        """
        ids: list[str] = [
            session["id"]
            for session in await self.fetch(kind=kind, status=status)
            if session["name"].startswith(prefix)
        ]
        return await self.destroy(ids)

    async def connect(self, ids: list[str] | str) -> None:
        """Connect to a session[s] in a web browser.

        Args:
            ids (Union[List[str], str]): Session ID[s].

        Examples:
            >>> from canfar.sessions import AsyncSession
            >>> session = AsyncSession()
            >>> await session.connect(id="hjko98yghj")
            >>> await session.connect(id=["hjko98yghj", "ikvp1jtp"])
        """
        if isinstance(ids, str):
            ids = [ids]
        info = await self.info(ids)
        for session in info:
            connect_url = session.get("connectURL")
            if connect_url:
                open_new_tab(connect_url)
