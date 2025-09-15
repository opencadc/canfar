"""Comprehensive tests for the session models module."""

import warnings

import pytest
from pydantic import ValidationError

from canfar.models.session import CreateRequest, FetchRequest


class TestCreateSpec:
    """Test CreateSpec class."""

    def test_required_fields(self) -> None:
        """Test CreateSpec with required fields only."""
        spec = CreateRequest(
            name="test-session",
            image="images.canfar.net/skaha/terminal:1.1.1",
            kind="headless",
        )

        assert spec.name == "test-session"
        assert spec.image == "images.canfar.net/skaha/terminal:1.1.1"
        assert spec.kind == "headless"
        assert spec.cores is None  # default
        assert spec.ram is None  # default
        assert spec.replicas == 1  # default
        assert spec.gpus is None
        assert spec.cmd is None
        assert spec.args is None
        assert spec.env is None

    def test_with_all_fields(self) -> None:
        """Test CreateSpec with all fields."""
        env_vars = {"FOO": "BAR", "DEBUG": "true"}

        spec = CreateRequest(
            name="full-session",
            image="custom/image:latest",
            kind="headless",
            cores=8,
            ram=16,
            gpus=2,
            cmd="python",
            args="script.py --verbose",
            env=env_vars,
            replicas=3,
        )

        assert spec.name == "full-session"
        assert spec.image == "images.canfar.net/custom/image:latest"  # Gets prefixed
        assert spec.kind == "headless"
        assert spec.cores == 8
        assert spec.ram == 16
        assert spec.gpus == 2
        assert spec.cmd == "python"
        assert spec.args == "script.py --verbose"
        assert spec.env == env_vars
        assert spec.replicas == 3

    def test_cores_validation(self) -> None:
        """Test cores field validation."""
        # Valid values
        spec = CreateRequest(name="test", image="skaha/test", kind="headless", cores=1)
        assert spec.cores == 1

        spec = CreateRequest(
            name="test", image="skaha/test", kind="headless", cores=256
        )
        assert spec.cores == 256

        # Invalid values
        with pytest.raises(ValidationError):
            CreateRequest(name="test", image="skaha/test", kind="headless", cores=0)

        with pytest.raises(ValidationError):
            CreateRequest(name="test", image="skaha/test", kind="headless", cores=257)

    def test_ram_validation(self) -> None:
        """Test RAM field validation."""
        # Valid values
        spec = CreateRequest(name="test", image="skaha/test", kind="headless", ram=1)
        assert spec.ram == 1

        spec = CreateRequest(name="test", image="skaha/test", kind="headless", ram=512)
        assert spec.ram == 512

        # Invalid values
        with pytest.raises(ValidationError):
            CreateRequest(name="test", image="skaha/test", kind="headless", ram=0)

        with pytest.raises(ValidationError):
            CreateRequest(name="test", image="skaha/test", kind="headless", ram=513)

    def test_gpus_validation(self) -> None:
        """Test GPUs field validation."""
        # Valid values
        spec = CreateRequest(name="test", image="skaha/test", kind="headless", gpus=1)
        assert spec.gpus == 1

        spec = CreateRequest(name="test", image="skaha/test", kind="headless", gpus=28)
        assert spec.gpus == 28

        # Invalid values
        with pytest.raises(ValidationError):
            CreateRequest(name="test", image="skaha/test", kind="headless", gpus=0)

        with pytest.raises(ValidationError):
            CreateRequest(name="test", image="skaha/test", kind="headless", gpus=29)

    def test_replicas_validation(self) -> None:
        """Test replicas field validation."""
        # Valid values
        spec = CreateRequest(
            name="test", image="skaha/test", kind="headless", replicas=1
        )
        assert spec.replicas == 1

        spec = CreateRequest(
            name="test", image="skaha/test", kind="headless", replicas=512
        )
        assert spec.replicas == 512

        # Invalid values
        with pytest.raises(ValidationError):
            CreateRequest(name="test", image="skaha/test", kind="headless", replicas=0)

        with pytest.raises(ValidationError):
            CreateRequest(
                name="test", image="skaha/test", kind="headless", replicas=513
            )

    def test_kind_validation(self) -> None:
        """Test kind field validation."""
        # Valid kinds
        valid_kinds = ["desktop", "notebook", "carta", "headless", "firefly"]
        for kind in valid_kinds:
            spec = CreateRequest(name="test", image="skaha/test", kind=kind)
            assert spec.kind == kind

        # Invalid kind
        with pytest.raises(ValidationError):
            CreateRequest(name="test", image="skaha/test", kind="invalid")

    def test_headless_validation_success(self) -> None:
        """Test that cmd, args, env are allowed for headless sessions."""
        spec = CreateRequest(
            name="test",
            image="skaha/test",
            kind="headless",
            cmd="python",
            args="script.py",
            env={"VAR": "value"},
        )

        assert spec.cmd == "python"
        assert spec.args == "script.py"
        assert spec.env == {"VAR": "value"}

    def test_non_headless_validation_failure(self) -> None:
        """Test that cmd, args, env are not allowed for non-headless sessions."""
        non_headless_kinds = ["desktop", "notebook", "carta", "firefly"]

        for kind in non_headless_kinds:
            # Test cmd restriction
            with pytest.raises(
                ValidationError, match="cmd, args, env only allowed for headless"
            ):
                CreateRequest(name="test", image="skaha/test", kind=kind, cmd="python")

            # Test args restriction
            with pytest.raises(
                ValidationError, match="cmd, args, env only allowed for headless"
            ):
                CreateRequest(
                    name="test", image="skaha/test", kind=kind, args="--verbose"
                )

            # Test env restriction
            with pytest.raises(
                ValidationError, match="cmd, args, env only allowed for headless"
            ):
                CreateRequest(
                    name="test", image="skaha/test", kind=kind, env={"VAR": "value"}
                )

    def test_firefly_desktop_warnings(self) -> None:
        """Test warnings for firefly and desktop sessions."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # Test firefly with ignored parameters
            CreateRequest(
                name="test",
                image="skaha/test",
                kind="firefly",
                cores=8,  # Should be ignored
                ram=16,  # Should be ignored
            )

            # Should have warnings about ignored parameters
            assert len(w) > 0
            assert "ignored for firefly sessions" in str(w[0].message)

    def test_firefly_desktop_replicas_validation(self) -> None:
        """Test that firefly and desktop sessions cannot have multiple replicas."""
        for kind in ["firefly", "desktop"]:
            with pytest.raises(
                ValidationError, match=f"multiple replicas invalid for {kind}"
            ):
                CreateRequest(
                    name="test",
                    image="skaha/test",
                    kind=kind,
                    replicas=2,
                )

    def test_serialization_alias(self) -> None:
        """Test that kind field uses 'type' as serialization alias."""
        spec = CreateRequest(name="test", image="skaha/test", kind="headless")

        # Test model dump with by_alias=True uses 'type' instead of 'kind'
        data = spec.model_dump(by_alias=True)
        assert "type" in data
        assert "kind" not in data
        assert data["type"] == "headless"

    def test_replicas_excluded_from_serialization(self) -> None:
        """Test that replicas field is excluded from serialization."""
        spec = CreateRequest(
            name="test", image="skaha/test", kind="headless", replicas=5
        )

        data = spec.model_dump()
        assert "replicas" not in data

        # But should be accessible directly
        assert spec.replicas == 5

    def test_populate_by_name(self) -> None:
        """Test that model can be populated by field name or alias."""
        # Using field name 'kind' (serialization_alias doesn't affect input)
        data = {"name": "test", "image": "skaha/test", "kind": "notebook"}
        spec = CreateRequest.model_validate(data)
        assert spec.kind == "notebook"

        # Test that the model config allows populate_by_name
        assert spec.model_config["populate_by_name"] is True


class TestFetchSpec:
    """Test FetchSpec class."""

    def test_default_values(self) -> None:
        """Test default values for FetchSpec."""
        spec = FetchRequest()

        assert spec.kind is None
        assert spec.status is None
        assert spec.view is None

    def test_with_all_values(self) -> None:
        """Test FetchSpec with all values."""
        spec = FetchRequest(
            type="headless",  # Using alias
            status="Running",
            view="all",
        )

        assert spec.kind == "headless"
        assert spec.status == "Running"
        assert spec.view == "all"

    def test_kind_validation(self) -> None:
        """Test kind field validation."""
        # Valid kinds
        valid_kinds = ["desktop", "notebook", "carta", "headless", "firefly"]
        for kind in valid_kinds:
            spec = FetchRequest(type=kind)  # Using alias
            assert spec.kind == kind

        # None is also valid (default)
        spec = FetchRequest()
        assert spec.kind is None

    def test_status_validation(self) -> None:
        """Test status field validation."""
        # Valid statuses
        valid_statuses = ["Pending", "Running", "Terminating", "Succeeded", "Error"]
        for status in valid_statuses:
            spec = FetchRequest(status=status)
            assert spec.status == status

        # None is also valid (default)
        spec = FetchRequest()
        assert spec.status is None

    def test_view_validation(self) -> None:
        """Test view field validation."""
        # Valid view
        spec = FetchRequest(view="all")
        assert spec.view == "all"

        # None is also valid (default)
        spec = FetchRequest()
        assert spec.view is None

    def test_kind_alias(self) -> None:
        """Test that kind field uses 'type' as alias."""
        # Using alias 'type'
        data = {"type": "notebook"}
        spec = FetchRequest.model_validate(data)
        assert spec.kind == "notebook"

        # Using field name 'kind' (with populate_by_name=True)
        data = {"kind": "notebook"}
        spec = FetchRequest.model_validate(data)
        assert spec.kind == "notebook"

    def test_populate_by_name(self) -> None:
        """Test that model can be populated by field name or alias."""
        # Test with all fields using aliases
        data = {"type": "headless", "status": "Running", "view": "all"}
        spec = FetchRequest.model_validate(data)
        assert spec.kind == "headless"
        assert spec.status == "Running"
        assert spec.view == "all"

    def test_model_config(self) -> None:
        """Test model configuration settings."""
        spec = FetchRequest()

        # Test that validate_assignment is enabled
        spec.kind = "notebook"
        assert spec.kind == "notebook"

        # Test that populate_by_name is enabled
        assert "populate_by_name" in spec.model_config
        assert spec.model_config["populate_by_name"] is True

    def test_image_validation_bare_names(self) -> None:
        """Test image validation for bare image names."""
        # Bare image name without tag
        spec = CreateRequest(name="test", image="skaha/astroml", kind="headless")
        assert spec.image == "images.canfar.net/skaha/astroml:latest"

        # Bare image name with tag
        spec = CreateRequest(name="test", image="skaha/astroml:v1.0", kind="headless")
        assert spec.image == "images.canfar.net/skaha/astroml:v1.0"

    def test_image_validation_canfar_registry(self) -> None:
        """Test image validation for CANFAR registry images."""
        # Full CANFAR registry path without tag
        spec = CreateRequest(
            name="test", image="images.canfar.net/skaha/astroml", kind="headless"
        )
        assert spec.image == "images.canfar.net/skaha/astroml:latest"

        # Full CANFAR registry path with tag
        spec = CreateRequest(
            name="test", image="images.canfar.net/skaha/astroml:v1.0", kind="headless"
        )
        assert spec.image == "images.canfar.net/skaha/astroml:v1.0"

    def test_image_validation_edge_cases(self) -> None:
        """Test edge cases for image validation."""
        # Image with complex tag
        spec = CreateRequest(
            name="test", image="skaha/astroml:v1.0-beta.1", kind="headless"
        )
        assert spec.image == "images.canfar.net/skaha/astroml:v1.0-beta.1"

        # Image with digest (should not get :latest appended)
        spec = CreateRequest(
            name="test", image="skaha/astroml@sha256:abc123", kind="headless"
        )
        assert spec.image == "images.canfar.net/skaha/astroml@sha256:abc123"


class TestSessionModelsIntegration:
    """Test integration between session models."""

    def test_create_and_fetch_spec_compatibility(self) -> None:
        """Test that CreateSpec and FetchSpec use compatible types."""
        # Create a session
        create_spec = CreateRequest(
            name="integration-test",
            image="skaha/test",
            kind="notebook",
        )

        # Fetch sessions of the same kind
        fetch_spec = FetchRequest(type=create_spec.kind)  # Using alias

        assert fetch_spec.kind == "notebook"
        assert fetch_spec.kind == create_spec.kind

    def test_all_kind_values_work(self) -> None:
        """Test that all Kind values work in both models."""
        valid_kinds = ["desktop", "notebook", "carta", "headless", "firefly"]

        for kind in valid_kinds:
            # Should work in CreateSpec
            create_spec = CreateRequest(name="test", image="skaha/test", kind=kind)
            assert create_spec.kind == kind

            # Should work in FetchSpec
            fetch_spec = FetchRequest(type=kind)  # Using alias
            assert fetch_spec.kind == kind

    def test_realistic_session_workflow(self) -> None:
        """Test a realistic session creation and fetching workflow."""
        # Create a headless session with custom parameters
        create_spec = CreateRequest(
            name="data-processing",
            image="skaha/python:3.9",
            kind="headless",
            cores=4,
            ram=8,
            cmd="python",
            args="process_data.py",
            env={"DATA_PATH": "/data", "OUTPUT_PATH": "/output"},
        )

        assert create_spec.name == "data-processing"
        assert (
            create_spec.image == "images.canfar.net/skaha/python:3.9"
        )  # Gets prefixed
        assert create_spec.kind == "headless"
        assert create_spec.cores == 4
        assert create_spec.ram == 8

        # Fetch running headless sessions
        fetch_spec = FetchRequest(type="headless", status="Running")  # Using alias

        assert fetch_spec.kind == "headless"
        assert fetch_spec.status == "Running"
