import unittest
import report_app


class TestUpdateRepositories(unittest.TestCase):
    def setUp(self):
        app = report_app.app
        app.config["TESTING"] = True
        self.ctx = app.app_context()
        self.ctx.push()
        self.client = app.test_client()
        self.index = "/update_repositories"
        self.json = {
            "name": "wp-ppo",
            "default_branch": "main",
            "url": "",
            "status": False,
            "report": {
                "has_default_branch_protection": True,
                "requires_approving_reviews": True,
                "administrators_require_review": False,
                "issues_section_enabled": True,
                "has_require_approvals_enabled": True,
                "has_license": True,
                "has_description": True
            },
            "last_push": "2023-05-17T08:50:26Z",
            "is_private": False,
        }

    def test_update_success(self):
        response = self.client.post(self.index, data=self.json, follow_redirects=True)

        self.assertEqual(response.status_code, 200)

    def test_update_fail(self):
        response = self.client.post(self.index, data={}, follow_redirects=True)

        self.assertEqual(response.json, {"status": "error"})
