import unittest
from landlordhq.app import create_app
from landlordhq.settings import DevConfig

class TenantControllerTestCase(unittest.TestCase):
    def setUp(self):
        """Set up the test client."""
        self.app = create_app()
        self.client = self.app.test_client()

    def test_tenant_with_id(self):
        """Test the /tenant/<tenant_id> endpoint."""
        response = self.client.get("/tenant/1")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"tenant view with tenant_id: 1", response.data)

    def test_tenant(self):
        """Test the /tenant endpoint."""
        response = self.client.get("/tenant")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"tenant view", response.data)

if __name__ == "__main__":
    unittest.main()