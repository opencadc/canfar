"""Comprehensive tests for the types module."""

from typing import get_args

from canfar.models.types import Kind, Mode, Status, View


class TestKindType:
    """Test Kind type alias."""

    def test_kind_values(self) -> None:
        """Test that Kind contains expected values."""
        expected_kinds = (
            "desktop",
            "notebook",
            "carta",
            "headless",
            "firefly",
            "desktop-app",
            "contributed",
        )
        actual_kinds = get_args(Kind)

        assert actual_kinds == expected_kinds

    def test_kind_completeness(self) -> None:
        """Test that all expected session kinds are included."""
        kinds = get_args(Kind)

        # Check that all common session types are present
        assert "desktop" in kinds
        assert "notebook" in kinds
        assert "carta" in kinds
        assert "headless" in kinds
        assert "firefly" in kinds
        assert "desktop-app" in kinds
        assert "contributed" in kinds


class TestStatusType:
    """Test Status type alias."""

    def test_status_values(self) -> None:
        """Test that Status contains expected values."""
        expected_statuses = (
            "Pending",
            "Running",
            "Terminating",
            "Succeeded",
            "Completed",
            "Error",
            "Failed",
        )
        actual_statuses = get_args(Status)

        assert actual_statuses == expected_statuses

    def test_status_completeness(self) -> None:
        """Test that all expected session statuses are included."""
        statuses = get_args(Status)

        # Check that all Kubernetes pod statuses are present
        assert "Pending" in statuses
        assert "Running" in statuses
        assert "Terminating" in statuses
        assert "Succeeded" in statuses
        assert "Completed" in statuses
        assert "Error" in statuses
        assert "Failed" in statuses

        # Check total count
        assert len(statuses) == 7

    def test_status_capitalization(self) -> None:
        """Test that Status values follow proper capitalization."""
        statuses = get_args(Status)

        for status in statuses:
            # All statuses should start with capital letter
            assert status[0].isupper()
            # Rest should be lowercase (except for proper nouns)
            assert status == status.capitalize() or status in ["Error"]


class TestViewType:
    """Test View type alias."""

    def test_view_values(self) -> None:
        """Test that View contains expected values."""
        expected_views = ("all",)
        actual_views = get_args(View)

        assert actual_views == expected_views

    def test_view_type_checking(self) -> None:
        """Test View type checking behavior."""
        # Valid view
        assert "all" in get_args(View)

    def test_view_completeness(self) -> None:
        """Test that View contains only expected value."""
        views = get_args(View)

        # Currently only "all" is supported
        assert "all" in views
        assert len(views) == 1

    def test_view_single_value(self) -> None:
        """Test that View currently has only one value."""
        views = get_args(View)
        assert len(views) == 1
        assert views[0] == "all"


class TestModeType:
    """Test Mode type alias."""

    def test_mode_values(self) -> None:
        """Test that Mode contains expected values."""
        expected_modes = ("x509", "oidc", "token", "default")
        actual_modes = get_args(Mode)

        assert actual_modes == expected_modes

    def test_mode_type_checking(self) -> None:
        """Test Mode type checking behavior."""
        # Valid modes
        valid_modes = ["x509", "oidc", "token", "default"]

        for mode in valid_modes:
            # These should be valid at runtime
            assert mode in get_args(Mode)

    def test_mode_completeness(self) -> None:
        """Test that all expected authentication modes are included."""
        modes = get_args(Mode)

        # Check that all authentication modes are present
        assert "x509" in modes
        assert "oidc" in modes
        assert "token" in modes
        assert "default" in modes

        # Check total count
        assert len(modes) == 4

    def test_mode_lowercase(self) -> None:
        """Test that Mode values are lowercase."""
        modes = get_args(Mode)

        for mode in modes:
            assert mode.islower()

    def test_mode_ordering(self) -> None:
        """Test that Mode values are in expected order."""
        modes = get_args(Mode)
        expected_order = ("x509", "oidc", "token", "default")

        assert modes == expected_order


class TestTypeAliasesIntegration:
    """Test integration between type aliases."""

    def test_all_types_are_literal(self) -> None:
        """Test that all type aliases are Literal types."""
        # All should have get_args() return tuples of strings
        assert isinstance(get_args(Kind), tuple)
        assert isinstance(get_args(Status), tuple)
        assert isinstance(get_args(View), tuple)
        assert isinstance(get_args(Mode), tuple)

        # All values should be strings
        for kind in get_args(Kind):
            assert isinstance(kind, str)

        for status in get_args(Status):
            assert isinstance(status, str)

        for view in get_args(View):
            assert isinstance(view, str)

        for mode in get_args(Mode):
            assert isinstance(mode, str)

    def test_no_overlapping_values(self) -> None:
        """Test that type aliases don't have overlapping values."""
        kind_values = set(get_args(Kind))
        status_values = set(get_args(Status))
        view_values = set(get_args(View))
        mode_values = set(get_args(Mode))

        # No overlap between Kind and Status
        assert kind_values.isdisjoint(status_values)

        # No overlap between Kind and View
        assert kind_values.isdisjoint(view_values)

        # No overlap between Kind and Mode
        assert kind_values.isdisjoint(mode_values)

        # No overlap between Status and View
        assert status_values.isdisjoint(view_values)

        # No overlap between Status and Mode
        assert status_values.isdisjoint(mode_values)

        # No overlap between View and Mode
        assert view_values.isdisjoint(mode_values)

    def test_type_alias_consistency(self) -> None:
        """Test that type aliases are consistently defined."""
        # All should be non-empty
        assert len(get_args(Kind)) > 0
        assert len(get_args(Status)) > 0
        assert len(get_args(View)) > 0
        assert len(get_args(Mode)) > 0

        # All values should be non-empty strings
        for type_alias in [Kind, Status, View, Mode]:
            for value in get_args(type_alias):
                assert isinstance(value, str)
                assert len(value) > 0
                assert value.strip() == value  # No leading/trailing whitespace

    def test_import_accessibility(self) -> None:
        """Test that all type aliases can be imported."""
        # This test ensures the imports work correctly
        # All should be accessible
        assert Kind is not None
        assert Status is not None
        assert View is not None
        assert Mode is not None


class TestTypeAliasUsage:
    """Test practical usage of type aliases."""

    def test_kind_in_function_annotation(self) -> None:
        """Test using Kind in function annotations."""

        def process_session(kind: Kind) -> str:
            return f"Processing {kind} session"

        # Should work with valid kinds
        for kind in get_args(Kind):
            result = process_session(kind)
            assert kind in result

    def test_status_in_function_annotation(self) -> None:
        """Test using Status in function annotations."""

        def check_status(status: Status) -> bool:
            return status in ["Running", "Succeeded"]

        # Should work with valid statuses
        assert check_status("Running") is True
        assert check_status("Succeeded") is True
        assert check_status("Pending") is False

    def test_view_in_function_annotation(self) -> None:
        """Test using View in function annotations."""

        def set_view(view: View) -> str:
            return f"View set to {view}"

        # Should work with valid view
        result = set_view("all")
        assert "all" in result

    def test_mode_in_function_annotation(self) -> None:
        """Test using Mode in function annotations."""

        def authenticate(mode: Mode) -> str:
            return f"Authenticating with {mode}"

        # Should work with valid modes
        for mode in get_args(Mode):
            result = authenticate(mode)
            assert mode in result
