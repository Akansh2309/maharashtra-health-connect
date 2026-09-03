# test_auth.py — tests for auth_utils and data_api
# run with: python3 -m pytest tests/ -v
# or:       python3 -m unittest tests/test_auth.py

import sys
import os
import unittest

# add project root to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import auth_utils
import data_api


class TestPasswords(unittest.TestCase):
    """Make sure hashing and verification actually work."""

    def test_same_input_same_hash(self):
        a = auth_utils.hash_pw("hello123")
        b = auth_utils.hash_pw("hello123")
        self.assertEqual(a, b)

    def test_different_input_different_hash(self):
        a = auth_utils.hash_pw("password1")
        b = auth_utils.hash_pw("password2")
        self.assertNotEqual(a, b)

    def test_check_correct_password(self):
        h = auth_utils.hash_pw("mysecret")
        self.assertTrue(auth_utils.check_pw("mysecret", h))

    def test_check_wrong_password(self):
        h = auth_utils.hash_pw("mysecret")
        self.assertFalse(auth_utils.check_pw("wrongguess", h))


class TestRegistration(unittest.TestCase):

    def setUp(self):
        # snapshot the user dict before each test
        self._backup = dict(auth_utils.USERS)

    def tearDown(self):
        # restore it after so tests don't leak state
        auth_utils.USERS.clear()
        auth_utils.USERS.update(self._backup)

    def test_register_new_user(self):
        uname, err = auth_utils.register("newguy", "new@test.com", "pass1234", "New Guy")
        self.assertIsNone(err)
        self.assertEqual(uname, "newguy")
        self.assertIn("newguy", auth_utils.USERS)

    def test_register_lowercases_username(self):
        uname, err = auth_utils.register("  BigName  ", "big@test.com", "pass1234", "Big")
        self.assertIsNone(err)
        self.assertEqual(uname, "bigname")

    def test_register_rejects_empty_fields(self):
        _, err = auth_utils.register("", "e@e.com", "pass", "Name")
        self.assertIn("required", err.lower())

    def test_register_rejects_short_username(self):
        _, err = auth_utils.register("ab", "ab@ab.com", "pass1234", "Name")
        self.assertIn("3", err)

    def test_register_rejects_short_password(self):
        _, err = auth_utils.register("validuser", "v@v.com", "abc", "Name")
        self.assertIn("4", err)

    def test_register_rejects_duplicate(self):
        _, err = auth_utils.register("akansh", "dupe@test.com", "pass1234", "Dupe")
        self.assertIn("taken", err.lower())

    def test_register_rejects_duplicate_email(self):
        _, err = auth_utils.register("someone", "akansh@kacchodis.org", "pass1234", "Someone")
        self.assertIn("email", err.lower())


class TestAuth(unittest.TestCase):

    def test_login_with_username(self):
        uname, err = auth_utils.authenticate("akansh", "admin123")
        self.assertIsNone(err)
        self.assertEqual(uname, "akansh")

    def test_login_with_email(self):
        uname, err = auth_utils.authenticate("akansh@kacchodis.org", "admin123")
        self.assertIsNone(err)
        self.assertEqual(uname, "akansh")

    def test_login_case_insensitive(self):
        uname, err = auth_utils.authenticate("AKANSH", "admin123")
        self.assertIsNone(err)

    def test_wrong_password(self):
        _, err = auth_utils.authenticate("akansh", "wrongpassword")
        self.assertIn("Invalid", err)

    def test_nonexistent_user(self):
        _, err = auth_utils.authenticate("nobody", "pass")
        self.assertIn("Invalid", err)

    def test_demo_login(self):
        uname, err = auth_utils.authenticate("demo", "demo")
        self.assertIsNone(err)
        self.assertEqual(uname, "demo")


class TestSessions(unittest.TestCase):

    def setUp(self):
        self._backup = dict(auth_utils.SESSIONS)

    def tearDown(self):
        auth_utils.SESSIONS.clear()
        auth_utils.SESSIONS.update(self._backup)

    def test_create_session_returns_sid_and_ttl(self):
        sid, ttl = auth_utils.create_session("akansh")
        self.assertIsInstance(sid, str)
        self.assertEqual(len(sid), 36)  # uuid4 format
        self.assertEqual(ttl, auth_utils.SESSION_TTL)

    def test_remember_me_gives_longer_ttl(self):
        _, ttl = auth_utils.create_session("akansh", remember=True)
        self.assertEqual(ttl, auth_utils.SESSION_TTL_REMEMBER)

    def test_session_stored(self):
        sid, _ = auth_utils.create_session("akansh")
        self.assertIn(sid, auth_utils.SESSIONS)
        self.assertEqual(auth_utils.SESSIONS[sid]["user"], "akansh")

    def test_session_info_logged_in(self):
        sid, _ = auth_utils.create_session("akansh")
        info = auth_utils.session_info(auth_utils.SESSIONS[sid])
        self.assertTrue(info["authenticated"])
        self.assertEqual(info["role"], "admin")

    def test_session_info_not_logged_in(self):
        info = auth_utils.session_info(None)
        self.assertFalse(info["authenticated"])


class TestCookies(unittest.TestCase):

    def test_make_cookie_format(self):
        c = auth_utils.make_cookie("abc-123", 3600)
        self.assertIn("mhc_session=abc-123", c)
        self.assertIn("Max-Age=3600", c)
        self.assertIn("HttpOnly", c)

    def test_expire_cookie(self):
        c = auth_utils.expire_cookie()
        self.assertIn("Max-Age=0", c)


class TestPathProtection(unittest.TestCase):

    def test_login_page_is_public(self):
        self.assertFalse(auth_utils.needs_auth("/login.html"))

    def test_api_login_is_public(self):
        self.assertFalse(auth_utils.needs_auth("/api/login"))

    def test_css_files_are_public(self):
        self.assertFalse(auth_utils.needs_auth("/css/style.css"))

    def test_dashboard_is_protected(self):
        self.assertTrue(auth_utils.needs_auth("/index.html"))

    def test_api_hospitals_is_protected(self):
        self.assertTrue(auth_utils.needs_auth("/api/hospitals"))


class TestDataApi(unittest.TestCase):

    def test_hospitals_loaded(self):
        hospitals = data_api.get_all_hospitals()
        self.assertIsInstance(hospitals, list)
        self.assertGreater(len(hospitals), 0)

    def test_get_hospital_by_valid_id(self):
        # grab first hospital's id
        first = data_api.get_all_hospitals()[0]
        result = data_api.get_hospital_by_id(first["id"])
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], first["id"])

    def test_get_hospital_invalid_id(self):
        result = data_api.get_hospital_by_id(999999)
        self.assertIsNone(result)

    def test_reviews_empty_initially(self):
        # use an id that no other test writes to
        reviews = data_api.get_reviews(9999)
        self.assertEqual(reviews, [])

    def test_add_review(self):
        first_id = data_api.get_all_hospitals()[0]["id"]
        fake_session = {"name": "Test User", "role": "user"}
        review = data_api.add_review(first_id, fake_session, 4, "Great hospital!")
        self.assertEqual(review["rating"], 4)
        self.assertEqual(review["name"], "Test User")

    def test_add_review_invalid_hospital(self):
        fake_session = {"name": "Test User", "role": "user"}
        with self.assertRaises(LookupError):
            data_api.add_review(999999, fake_session, 3, "nope")


class TestRbac(unittest.TestCase):

    def test_admin_passes_any_role(self):
        sess = {"role": "admin"}
        self.assertTrue(auth_utils.has_role(sess, "user"))
        self.assertTrue(auth_utils.has_role(sess, "admin"))

    def test_user_only_passes_user_role(self):
        sess = {"role": "user"}
        self.assertTrue(auth_utils.has_role(sess, "user"))
        self.assertFalse(auth_utils.has_role(sess, "moderator"))

    def test_none_session_fails(self):
        self.assertFalse(auth_utils.has_role(None, "user"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
