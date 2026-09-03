import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import auth_utils


class TestPasswordHashing(unittest.TestCase):

    def test_hash_produces_consistent_output(self):
        h1 = auth_utils.hash_password("testpass")
        h2 = auth_utils.hash_password("testpass")
        self.assertEqual(h1, h2)

    def test_different_passwords_produce_different_hashes(self):
        h1 = auth_utils.hash_password("password1")
        h2 = auth_utils.hash_password("password2")
        self.assertNotEqual(h1, h2)

    def test_verify_correct_password(self):
        hashed = auth_utils.hash_password("secure123")
        self.assertTrue(auth_utils.verify_password("secure123", hashed))

    def test_verify_wrong_password(self):
        hashed = auth_utils.hash_password("secure123")
        self.assertFalse(auth_utils.verify_password("wrong", hashed))


class TestUserRegistration(unittest.TestCase):

    def setUp(self):
        self._original_users = dict(auth_utils.USERS)

    def tearDown(self):
        auth_utils.USERS.clear()
        auth_utils.USERS.update(self._original_users)

    def test_register_valid_user(self):
        username, error = auth_utils.register_user("testuser", "pass1234", "Test User")
        self.assertIsNone(error)
        self.assertEqual(username, "testuser")
        self.assertIn("testuser", auth_utils.USERS)

    def test_register_strips_and_lowercases_username(self):
        username, error = auth_utils.register_user("  TestUser  ", "pass1234", "Test")
        self.assertIsNone(error)
        self.assertEqual(username, "testuser")

    def test_register_rejects_empty_fields(self):
        username, error = auth_utils.register_user("", "pass", "Name")
        self.assertIsNone(username)
        self.assertIn("required", error.lower())

    def test_register_rejects_short_username(self):
        username, error = auth_utils.register_user("ab", "pass1234", "Name")
        self.assertIsNone(username)
        self.assertIn("3", error)

    def test_register_rejects_short_password(self):
        username, error = auth_utils.register_user("validuser", "abc", "Name")
        self.assertIsNone(username)
        self.assertIn("4", error)

    def test_register_rejects_duplicate_username(self):
        username, error = auth_utils.register_user("akansh", "pass1234", "Duplicate")
        self.assertIsNone(username)
        self.assertIn("taken", error.lower())


class TestAuthentication(unittest.TestCase):

    def test_login_valid_credentials(self):
        username, error = auth_utils.authenticate_user("akansh", "admin123")
        self.assertIsNone(error)
        self.assertEqual(username, "akansh")

    def test_login_demo_account(self):
        username, error = auth_utils.authenticate_user("demo", "demo")
        self.assertIsNone(error)
        self.assertEqual(username, "demo")

    def test_login_wrong_password(self):
        username, error = auth_utils.authenticate_user("akansh", "wrongpass")
        self.assertIsNone(username)
        self.assertIn("Invalid", error)

    def test_login_nonexistent_user(self):
        username, error = auth_utils.authenticate_user("nobody", "pass")
        self.assertIsNone(username)
        self.assertIn("Invalid", error)

    def test_login_case_insensitive(self):
        username, error = auth_utils.authenticate_user("AKANSH", "admin123")
        self.assertIsNone(error)
        self.assertEqual(username, "akansh")


class TestSessionManagement(unittest.TestCase):

    def setUp(self):
        self._original_sessions = dict(auth_utils.SESSIONS)

    def tearDown(self):
        auth_utils.SESSIONS.clear()
        auth_utils.SESSIONS.update(self._original_sessions)

    def test_create_session_returns_sid_and_ttl(self):
        sid, ttl = auth_utils.create_session("akansh")
        self.assertIsInstance(sid, str)
        self.assertEqual(len(sid), 36)
        self.assertEqual(ttl, auth_utils.SESSION_TTL)

    def test_create_session_with_remember(self):
        sid, ttl = auth_utils.create_session("akansh", remember=True)
        self.assertEqual(ttl, auth_utils.SESSION_TTL_REMEMBER)

    def test_session_stored_in_memory(self):
        sid, _ = auth_utils.create_session("akansh")
        self.assertIn(sid, auth_utils.SESSIONS)
        self.assertEqual(auth_utils.SESSIONS[sid]["user"], "akansh")

    def test_get_session_info_authenticated(self):
        sid, _ = auth_utils.create_session("akansh")
        session = auth_utils.SESSIONS[sid]
        info = auth_utils.get_session_info(session)
        self.assertTrue(info["authenticated"])
        self.assertEqual(info["user"], "akansh")
        self.assertEqual(info["role"], "admin")

    def test_get_session_info_none(self):
        info = auth_utils.get_session_info(None)
        self.assertFalse(info["authenticated"])


class TestCookieHelpers(unittest.TestCase):

    def test_build_set_cookie_format(self):
        cookie = auth_utils.build_set_cookie("abc-123", 3600)
        self.assertIn("mhc_session=abc-123", cookie)
        self.assertIn("Path=/", cookie)
        self.assertIn("Max-Age=3600", cookie)

    def test_build_expire_cookie_format(self):
        cookie = auth_utils.build_expire_cookie()
        self.assertIn("mhc_session=", cookie)
        self.assertIn("Max-Age=0", cookie)

    def test_parse_cookies(self):
        result = auth_utils.parse_cookies("mhc_session=abc123; theme=dark")
        self.assertEqual(result["mhc_session"], "abc123")
        self.assertEqual(result["theme"], "dark")

    def test_parse_empty_cookies(self):
        result = auth_utils.parse_cookies("")
        self.assertEqual(result, {})


class TestPathProtection(unittest.TestCase):

    def test_login_page_is_public(self):
        self.assertFalse(auth_utils.is_path_protected("/login.html"))

    def test_api_login_is_public(self):
        self.assertFalse(auth_utils.is_path_protected("/api/login"))

    def test_api_register_is_public(self):
        self.assertFalse(auth_utils.is_path_protected("/api/register"))

    def test_dashboard_is_protected(self):
        self.assertTrue(auth_utils.is_path_protected("/index.html"))

    def test_api_hospitals_is_protected(self):
        self.assertTrue(auth_utils.is_path_protected("/api/hospitals"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
