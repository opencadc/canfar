"""Tests for the build utilities module."""

from canfar.utils.build import create_parameters, fetch_parameters


class TestFetchParameters:
    """Test the fetch_parameters function."""

    def test_fetch_parameters_empty(self) -> None:
        """Test fetch_parameters with no arguments."""
        result = fetch_parameters()
        assert result == {}

    def test_fetch_parameters_with_kind(self) -> None:
        """Test fetch_parameters with kind."""
        result = fetch_parameters(kind="headless")
        assert result == {"type": "headless"}  # kind becomes type due to alias

    def test_fetch_parameters_with_all(self) -> None:
        """Test fetch_parameters with all parameters."""
        result = fetch_parameters(kind="notebook", status="Running", view="all")
        assert result == {"type": "notebook", "status": "Running", "view": "all"}


class TestCreateParameters:
    """Test the create_parameters function."""

    def test_create_parameters_basic(self) -> None:
        """Test create_parameters with basic required parameters."""
        result = create_parameters(
            name="test-session", image="images.canfar.net/skaha/terminal:1.1.1"
        )

        assert len(result) == 1  # Single replica
        payload = result[0]

        # Convert list of tuples to dict for easier testing
        payload_dict = dict(payload)

        assert payload_dict["name"] == "test-session"
        assert payload_dict["image"] == "images.canfar.net/skaha/terminal:1.1.1"
        assert payload_dict["type"] == "headless"  # default kind becomes type
        assert payload_dict.get("cores") is None  # default
        assert payload_dict.get("ram") is None  # default
        assert "cores" not in payload_dict
        assert "ram" not in payload_dict
        # Check environment variables - they are stored as list of "KEY=VALUE" strings
        env_items = [item for key, item in payload if key == "env"]
        env_vars = dict([item.split("=", 1) for item in env_items])
        assert env_vars["REPLICA_ID"] == "1"
        assert env_vars["REPLICA_COUNT"] == "1"

    def test_create_parameters_without_env(self) -> None:
        """Test create_parameters without providing env parameter (covers line 60)."""
        result = create_parameters(
            name="test-session",
            image="images.canfar.net/skaha/terminal:1.1.1",
            env=None,  # Explicitly no env
        )

        assert len(result) == 1
        payload = result[0]

        # Should still have env with replica variables
        env_items = [item for key, item in payload if key == "env"]
        env_vars = dict([item.split("=", 1) for item in env_items])
        assert env_vars["REPLICA_ID"] == "1"
        assert env_vars["REPLICA_COUNT"] == "1"

    def test_create_parameters_multiple_replicas(self) -> None:
        """Test create_parameters with multiple replicas (covers line 65)."""
        result = create_parameters(
            name="test-session",
            image="images.canfar.net/skaha/terminal:1.1.1",
            replicas=3,
        )

        assert len(result) == 3  # Three replicas

        # Check each replica has correct naming
        for i, payload in enumerate(result):
            payload_dict = dict(payload)
            expected_name = f"test-session-{i + 1}"
            assert payload_dict["name"] == expected_name

            # Check environment variables
            env_items = [item for key, item in payload if key == "env"]
            env_vars = dict([item.split("=", 1) for item in env_items])
            assert env_vars["REPLICA_ID"] == str(i + 1)
            assert env_vars["REPLICA_COUNT"] == "3"

    def test_create_parameters_single_replica_naming(self) -> None:
        """Test create_parameters with single replica keeps original name."""
        result = create_parameters(
            name="test-session",
            image="images.canfar.net/skaha/terminal:1.1.1",
            replicas=1,
        )

        assert len(result) == 1
        payload = result[0]
        payload_dict = dict(payload)

        # Single replica should keep original name (not test-session-1)
        assert payload_dict["name"] == "test-session"

    def test_create_parameters_with_env(self) -> None:
        """Test create_parameters with custom environment variables."""
        custom_env = {"CUSTOM_VAR": "custom_value", "DEBUG": "true"}
        result = create_parameters(
            name="test-session",
            image="images.canfar.net/skaha/terminal:1.1.1",
            env=custom_env,
        )

        assert len(result) == 1
        payload = result[0]

        # Check that custom env vars are included along with replica vars
        env_items = [item for key, item in payload if key == "env"]
        env_vars = dict([item.split("=", 1) for item in env_items])
        assert env_vars["CUSTOM_VAR"] == "custom_value"
        assert env_vars["DEBUG"] == "true"
        assert env_vars["REPLICA_ID"] == "1"
        assert env_vars["REPLICA_COUNT"] == "1"

    def test_create_parameters_all_options(self) -> None:
        """Test create_parameters with all optional parameters for headless."""
        result = create_parameters(
            name="full-session",
            image="custom/image:latest",
            cores=8,
            ram=16,
            kind="headless",  # Use headless to allow cmd, args, env
            gpu=2,
            cmd="python",
            args="script.py --verbose",
            env={"FOO": "BAR"},
            replicas=2,
        )

        assert len(result) == 2  # Two replicas

        for i, payload in enumerate(result):
            payload_dict = dict(payload)

            # Check basic parameters
            assert payload_dict["name"] == f"full-session-{i + 1}"
            assert payload_dict["image"] == "images.canfar.net/custom/image:latest"
            assert payload_dict["cores"] == 8
            assert payload_dict["ram"] == 16
            assert payload_dict["type"] == "headless"  # kind becomes type
            assert payload_dict["gpus"] == 2  # gpu becomes gpus
            assert payload_dict["cmd"] == "python"
            assert payload_dict["args"] == "script.py --verbose"

            # Check environment variables
            env_items = [item for key, item in payload if key == "env"]
            env_vars = dict([item.split("=", 1) for item in env_items])
            assert env_vars["FOO"] == "BAR"
            assert env_vars["REPLICA_ID"] == str(i + 1)
            assert env_vars["REPLICA_COUNT"] == "2"
