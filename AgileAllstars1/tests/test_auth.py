"""
Test Case 1 - Login and Authentication  (F1-001 through F1-005)

We need a registered PM user to already exist in the DB, and the
login page has to be up at /login/.  We clear the cache before each
test so the lockout counter doesn't carry over.
"""

from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse

from users.views import sign_in


class LoginAuthenticationTests(TestCase):
    """Hit the login page with good creds, bad creds, empty fields,
    and a bunch of wrong passwords to trigger lockout."""

    databases = '__all__'

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='pm_user', email='pm@company.com', password='Test@1234!'
        )

    def setUp(self):
        self.client = Client()
        self.login_url = reverse('login')
        cache.clear()

    # -- F1-001: Log in with the right username and password --
    def test_F1_001_successful_login(self):
        """Should redirect to the project dashboard and be authenticated."""
        response = self.client.post(
            self.login_url,
            {'username': 'pm_user', 'password': 'Test@1234!'},
        )
        self.assertRedirects(response, reverse('project_list'))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    # -- F1-002: Try logging in with the wrong password --
    def test_F1_002_wrong_password(self):
        """Should show an error and NOT let us in."""
        response = self.client.post(
            self.login_url,
            {'username': 'pm_user', 'password': 'WrongPass!'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password')
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    # -- F1-003: Try a username that doesn't exist at all --
    def test_F1_003_unregistered_user(self):
        """Same error message, no login."""
        response = self.client.post(
            self.login_url,
            {'username': 'ghost_user', 'password': 'AnyPass!'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password')
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    # -- F1-004: Submit the form with nothing filled in --
    def test_F1_004_empty_fields(self):
        """Both fields blank — form should catch it, no login."""
        response = self.client.post(self.login_url, {'username': '', 'password': ''})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_F1_004b_empty_password_only(self):
        """Username filled in but password blank — still no login."""
        response = self.client.post(self.login_url, {'username': 'pm_user', 'password': ''})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    # -- F1-005: Hammer the login with wrong passwords to trigger lockout --
    def test_F1_005_account_lockout_after_failed_attempts(self):
        """After 5 bad tries, the 6th should show the lockout message."""
        for _ in range(5):
            self.client.post(
                self.login_url,
                {'username': 'pm_user', 'password': 'WrongPass!'},
            )
        response = self.client.post(
            self.login_url,
            {'username': 'pm_user', 'password': 'WrongPass!'},
        )
        self.assertContains(response, 'Too many failed attempts')

    def test_F1_005b_lockout_blocks_correct_password(self):
        """Even if you finally type the RIGHT password, you're still locked out."""
        for _ in range(5):
            self.client.post(
                self.login_url,
                {'username': 'pm_user', 'password': 'WrongPass!'},
            )
        response = self.client.post(
            self.login_url,
            {'username': 'pm_user', 'password': 'Test@1234!'},
        )
        self.assertContains(response, 'Too many failed attempts')
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_F1_005c_successful_login_resets_counter(self):
        """If you log in successfully before hitting 5, the counter resets."""
        # Fail 3 times
        for _ in range(3):
            self.client.post(
                self.login_url,
                {'username': 'pm_user', 'password': 'WrongPass!'},
            )
        # Succeed — this should reset the counter back to 0
        self.client.post(
            self.login_url,
            {'username': 'pm_user', 'password': 'Test@1234!'},
        )
        # Fail 4 more times (still under the limit since we reset)
        for _ in range(4):
            self.client.post(
                self.login_url,
                {'username': 'pm_user', 'password': 'WrongPass!'},
            )
        # This should still work because we only have 4 fails, not 5
        response = self.client.post(
            self.login_url,
            {'username': 'pm_user', 'password': 'Test@1234!'},
        )
        self.assertRedirects(response, reverse('project_list'))


class LoginRequestFactoryTests(TestCase):
    """Lower-level tests using RequestFactory to hit sign_in directly."""

    databases = '__all__'

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='pm_user', email='pm@company.com', password='Test@1234!'
        )

    def setUp(self):
        self.factory = RequestFactory()

    def test_get_returns_login_form(self):
        """GET /login/ should give us back the login form page."""
        request = self.factory.get(reverse('login'))
        from django.contrib.sessions.middleware import SessionMiddleware
        from django.contrib.auth.models import AnonymousUser
        middleware = SessionMiddleware(lambda r: None)
        middleware.process_request(request)
        request.session.save()
        request.user = AnonymousUser()
        response = sign_in(request)
        self.assertEqual(response.status_code, 200)

    def test_authenticated_user_redirect_via_client(self):
        """If you're already logged in and go to /login/, bounce to dashboard."""
        client = Client()
        client.login(username='pm_user', password='Test@1234!')
        response = client.get(reverse('login'))
        self.assertRedirects(response, reverse('project_list'))


class LogoutTests(TestCase):
    """Make sure logout actually logs you out and clears the session."""

    databases = '__all__'

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='pm_user', email='pm@company.com', password='Test@1234!'
        )

    def test_logout_redirects_to_login(self):
        self.client.login(username='pm_user', password='Test@1234!')
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('login'))

    def test_logout_clears_session(self):
        """After logging out, trying to hit the dashboard should
        bounce us back to the login page."""
        self.client.login(username='pm_user', password='Test@1234!')
        self.client.get(reverse('logout'))
        response = self.client.get(reverse('project_list'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('project_list')}")


class RegistrationTests(TestCase):
    """Test the sign-up flow — good data, bad data, duplicates."""

    databases = '__all__'

    def test_register_get_shows_form(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)

    def test_register_valid_user(self):
        """Fill in everything correctly — should create the user and
        redirect to login."""
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'new@company.com',
            'password1': 'Str0ngP@ss!',
            'password2': 'Str0ngP@ss!',
        })
        self.assertRedirects(response, reverse('login'))
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_password_mismatch(self):
        """Passwords don't match — user should NOT be created."""
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'new@company.com',
            'password1': 'Str0ngP@ss!',
            'password2': 'DifferentPass!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='newuser').exists())

    def test_register_duplicate_username(self):
        """Username already taken — should get rejected."""
        User.objects.create_user(username='existinguser', password='Pass@1234!')
        response = self.client.post(reverse('register'), {
            'username': 'existinguser',
            'email': 'dup@company.com',
            'password1': 'Str0ngP@ss!',
            'password2': 'Str0ngP@ss!',
        })
        self.assertEqual(response.status_code, 200)
