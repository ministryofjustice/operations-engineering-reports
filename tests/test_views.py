import unittest
import report_app

class TestUpdateRepositories(unittest.TestCase):
        def setUp(self):
            app = report_app.app
            app.config["TESTING"] = True
            self.ctx = app.app_context()
            self.ctx.push()
            self.client = app.test_client()
            self.index = "/index"

        def test_update_repositories():
            response = self.client.post(self.index, data={
                "name": "wp-ppo",
                "default_branch": "main",
                "url": ""
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
            })

            self.assertEqual(response.status_code, 200)





            assert True

