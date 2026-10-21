import unittest

from backend.app.shared.azure.azure_search_service import AzureSearchService


class AzureSearchAclFilterTest(unittest.TestCase):

    def test_builds_group_department_and_sensitivity_filter(self):
        result = AzureSearchService.build_acl_filter(
            group_ids=["group-1", "group-2"],
            permissions=[
                {"department": "Legal", "max_sensitivity": 2},
                {"department": "Finance", "max_sensitivity": 3},
            ],
        )

        print(f"[TEST][ACL] generated_filter={result}")
        self.assertEqual(
            result,
            "(allowed_group_ids/any("
            "g: g eq 'group-1' or g eq 'group-2'"
            ")) and ((department eq 'Legal' and sensitivity le 2) or "
            "(department eq 'Finance' and sensitivity le 3))",
        )

    def test_escapes_deduplicates_and_uses_highest_permission(self):
        result = AzureSearchService.build_acl_filter(
            group_ids=["group'id", "group'id", ""],
            permissions=[
                {"department": "R&D's", "max_sensitivity": 1},
                {"department": "R&D's", "max_sensitivity": 4},
            ],
        )

        print(f"[TEST][ACL] normalized_filter={result}")
        self.assertEqual(result.count("g eq 'group''id'"), 1)
        self.assertIn("department eq 'R&D''s'", result)
        self.assertIn("sensitivity le 4", result)
        self.assertNotIn("sensitivity le 1", result)

    def test_rejects_empty_groups(self):
        print("[TEST][ACL] expecting rejection for empty group_ids")
        with self.assertRaisesRegex(ValueError, "group_ids"):
            AzureSearchService.build_acl_filter(
                group_ids=[],
                permissions=[
                    {"department": "Legal", "max_sensitivity": 2},
                ],
            )

    def test_rejects_empty_valid_permissions(self):
        print("[TEST][ACL] expecting rejection for empty permissions")
        with self.assertRaisesRegex(ValueError, "permissions"):
            AzureSearchService.build_acl_filter(
                group_ids=["group-1"],
                permissions=[
                    {"department": "", "max_sensitivity": 2},
                    {"department": "Legal", "max_sensitivity": "bad"},
                ],
            )
