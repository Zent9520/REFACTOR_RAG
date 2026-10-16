import unittest

from backend.app.shared.azure.azure_search_service import AzureSearchService


class AzureSearchAclFilterTest(unittest.TestCase):

    def test_builds_user_and_group_acl_filter(self):
        result = AzureSearchService.build_acl_filter(
            user_object_id="user-id",
            group_ids=["group-1", "group-2"],
        )

        self.assertEqual(
            result,
            "allowed_user_ids/any(u: u eq 'user-id') or "
            "allowed_group_ids/any("
            "g: g eq 'group-1' or g eq 'group-2'"
            ")",
        )

    def test_user_acl_remains_when_groups_are_empty(self):
        result = AzureSearchService.build_acl_filter(
            user_object_id="user-id",
            group_ids=[],
        )

        self.assertEqual(
            result,
            "allowed_user_ids/any(u: u eq 'user-id')",
        )

    def test_escapes_values_and_removes_duplicate_groups(self):
        result = AzureSearchService.build_acl_filter(
            user_object_id="user'id",
            group_ids=["group'id", "group'id", ""],
        )

        self.assertIn("u eq 'user''id'", result)
        self.assertEqual(result.count("g eq 'group''id'"), 1)

    def test_rejects_empty_user_id_instead_of_unrestricted_filter(self):
        with self.assertRaises(ValueError):
            AzureSearchService.build_acl_filter(
                user_object_id=" ",
                group_ids=[],
            )
