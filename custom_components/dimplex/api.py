"""Async API client for Dimplex heat pumps."""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlencode, urlparse, parse_qs, quote_plus

import aiohttp
from aiohttp import ClientResponseError, ClientError

from .const import (
    API_BASE_URL,
    API_USER_AGENT,
    OAUTH2_AUTHORIZE_URL,
    OAUTH2_TOKEN_URL,
    OAUTH2_CLIENT_ID,
    OAUTH2_REDIRECT_URI,
    OAUTH2_SCOPE,
    ALL_VARIABLE_IDS,
)

_LOGGER = logging.getLogger(__name__)

# Token refresh buffer - refresh 5 minutes before expiry
TOKEN_EXPIRY_BUFFER = timedelta(minutes=5)

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds


class DimplexAuthError(Exception):
    """Authentication error."""


class DimplexApiError(Exception):
    """API error."""


class DimplexLoginError(Exception):
    """Login error with username/password."""


async def get_devices(
    access_token: str,
    session: aiohttp.ClientSession | None = None,
) -> dict[str, dict]:
    """
    Get list of devices associated with the account.

    Returns dict mapping device_id to device info (displayName, deviceType, etc.)
    """
    own_session = session is None
    if session is None:
        session = aiohttp.ClientSession()

    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "User-Agent": API_USER_AGENT,
        }

        async with session.get(
            f"{API_BASE_URL}/devices/",
            headers=headers,
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                _LOGGER.error("Failed to get devices: %s - %s", response.status, error_text)
                raise DimplexApiError(f"Failed to get devices: {response.status}")

            data = await response.json()

            # Parse device info
            devices = {}
            for device_id, device_info in data.items():
                display_name = device_info.get("displayName", device_id)
                device_type = device_info.get("deviceType", {})
                type_name = device_type.get("typeName", "Unknown")

                devices[device_id] = {
                    "display_name": display_name,
                    "type_name": type_name,
                    "connection_status": device_info.get("connectionStatus", "Unknown"),
                    "gateway_mac": device_info.get("gatewayMac", ""),
                }
                _LOGGER.debug("Found device: %s (%s) - %s", display_name, type_name, device_id)

            return devices

    finally:
        if own_session:
            await session.close()


class DimplexApiClient:
    """Async API client for Dimplex."""

    def __init__(
        self,
        device_id: str,
        access_token: str,
        refresh_token: str,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        """Initialize the API client."""
        self._device_id = device_id
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._session = session
        self._own_session = session is None
        self._token_expires_at: datetime | None = None
        self._token_lock = asyncio.Lock()

    @property
    def device_id(self) -> str:
        """Return the device ID."""
        return self._device_id

    @property
    def access_token(self) -> str:
        """Return current access token."""
        return self._access_token

    @property
    def refresh_token(self) -> str:
        """Return current refresh token."""
        return self._refresh_token

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            self._own_session = True
        return self._session

    async def close(self) -> None:
        """Close the session if we own it."""
        if self._own_session and self._session and not self._session.closed:
            await self._session.close()

    def _get_headers(self) -> dict[str, str]:
        """Get headers for API requests."""
        return {
            "Authorization": f"Bearer {self._access_token}",
            "User-Agent": API_USER_AGENT,
            "Content-Type": "application/json",
        }

    async def _refresh_access_token(self) -> None:
        """Refresh the access token using the refresh token."""
        async with self._token_lock:
            _LOGGER.debug("Refreshing access token")
            session = await self._get_session()

            payload = {
                "grant_type": "refresh_token",
                "client_id": OAUTH2_CLIENT_ID,
                "client_secret": "",
                "redirect_uri": OAUTH2_REDIRECT_URI,
                "refresh_token": self._refresh_token,
            }

            try:
                async with session.post(
                    OAUTH2_TOKEN_URL,
                    data=payload,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        _LOGGER.error(
                            "Token refresh failed: %s - %s",
                            response.status,
                            error_text,
                        )
                        raise DimplexAuthError(
                            f"Token refresh failed: {response.status}"
                        )

                    data = await response.json()
                    self._access_token = data["access_token"]
                    self._refresh_token = data.get("refresh_token", self._refresh_token)

                    # Parse token expiry (usually 1 hour)
                    expires_in = data.get("expires_in", 3600)
                    self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)

                    _LOGGER.debug(
                        "Token refreshed, expires at %s",
                        self._token_expires_at,
                    )

            except aiohttp.ClientError as err:
                _LOGGER.error("Network error during token refresh: %s", err)
                raise DimplexAuthError(f"Network error: {err}") from err

    async def _ensure_valid_token(self) -> None:
        """Ensure we have a valid access token."""
        if self._token_expires_at is None:
            # First run, refresh to get expiry info
            await self._refresh_access_token()
        elif datetime.now() >= self._token_expires_at - TOKEN_EXPIRY_BUFFER:
            # Token expiring soon, refresh
            await self._refresh_access_token()

    async def _api_request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        retry_on_auth_error: bool = True,
    ) -> dict[str, Any]:
        """Make an API request with automatic retry and token refresh."""
        await self._ensure_valid_token()
        session = await self._get_session()
        url = f"{API_BASE_URL}{endpoint}"

        for attempt in range(MAX_RETRIES):
            try:
                _LOGGER.debug(
                    "API request: %s %s (attempt %d)",
                    method,
                    endpoint,
                    attempt + 1,
                )

                async with session.request(
                    method,
                    url,
                    json=data,
                    headers=self._get_headers(),
                ) as response:
                    if response.status == 401:
                        if retry_on_auth_error:
                            _LOGGER.debug("Got 401, refreshing token and retrying")
                            # Force token refresh
                            self._token_expires_at = None
                            await self._refresh_access_token()
                            # Retry without auth error handling to prevent infinite loop
                            return await self._api_request(
                                method, endpoint, data, retry_on_auth_error=False
                            )
                        raise DimplexAuthError("Authentication failed after token refresh")

                    if response.status >= 400:
                        error_text = await response.text()
                        _LOGGER.error(
                            "API error: %s - %s",
                            response.status,
                            error_text,
                        )
                        raise DimplexApiError(
                            f"API request failed: {response.status}"
                        )

                    return await response.json()

            except aiohttp.ClientError as err:
                _LOGGER.warning(
                    "Network error (attempt %d/%d): %s",
                    attempt + 1,
                    MAX_RETRIES,
                    err,
                )
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                else:
                    raise DimplexApiError(f"Network error after {MAX_RETRIES} retries: {err}") from err

        raise DimplexApiError("Max retries exceeded")

    async def read_variables(
        self, variable_ids: list[str] | None = None
    ) -> dict[str, Any]:
        """Read variables from the heat pump."""
        if variable_ids is None:
            variable_ids = ALL_VARIABLE_IDS

        endpoint = f"/devices/{self._device_id}/wpm/variable_read"
        data = {"variableIds": variable_ids}

        return await self._api_request("POST", endpoint, data)

    async def write_variable(self, variable_id: str, value: int | str) -> dict[str, Any]:
        """Write a variable to the heat pump."""
        endpoint = f"/devices/{self._device_id}/wpm/variable_write"
        data = {variable_id: value}

        _LOGGER.debug("Writing variable %s = %s", variable_id, value)
        return await self._api_request("POST", endpoint, data)

    async def set_ventilation_bypass(self, enabled: bool) -> bool:
        """Set ventilation bypass to the desired state.

        The hardware edge-triggers on writes of 1 to VENTILATION_BYPASS_SWITCH
        (2212i): each such write flips the bypass regardless of the previous
        state. The actual state lives in VENT_BYPASS_STATUS (2214i), which
        reports 0 when off and a non-zero value (observed: 10) when on. After
        triggering we reset 2212i to 0 so the next write of 1 is detected
        as a fresh edge.
        """
        from .const import (
            VarID,
            BYPASS_TOGGLE_POLL_INTERVAL,
            BYPASS_TOGGLE_TIMEOUT,
        )

        def _is_active(raw: Any) -> bool | None:
            if raw is None:
                return None
            try:
                return int(float(raw)) != 0
            except (ValueError, TypeError):
                return None

        current_data = await self.read_variables([VarID.VENT_BYPASS_STATUS])
        current = _is_active(current_data.get(VarID.VENT_BYPASS_STATUS, {}).get("value"))

        if current == enabled:
            _LOGGER.debug("Bypass already %s, nothing to do", "on" if enabled else "off")
            return True

        _LOGGER.debug(
            "Triggering bypass toggle (current=%s, target=%s)",
            "on" if current else "off",
            "on" if enabled else "off",
        )
        await self.write_variable(VarID.VENTILATION_BYPASS_SWITCH, 1)

        state_changed = False
        elapsed = 0
        try:
            while elapsed < BYPASS_TOGGLE_TIMEOUT:
                await asyncio.sleep(BYPASS_TOGGLE_POLL_INTERVAL)
                elapsed += BYPASS_TOGGLE_POLL_INTERVAL
                data = await self.read_variables([VarID.VENT_BYPASS_STATUS])
                new_state = _is_active(data.get(VarID.VENT_BYPASS_STATUS, {}).get("value"))
                if new_state == enabled:
                    _LOGGER.debug(
                        "Bypass flipped to %s after %ds",
                        "on" if enabled else "off",
                        elapsed,
                    )
                    state_changed = True
                    break
        finally:
            try:
                await self.write_variable(VarID.VENTILATION_BYPASS_SWITCH, 0)
            except DimplexApiError as err:
                _LOGGER.warning("Failed to reset bypass trigger flag: %s", err)

        if not state_changed:
            _LOGGER.warning(
                "Bypass did not reach state %s within %ds",
                "on" if enabled else "off",
                BYPASS_TOGGLE_TIMEOUT,
            )

        return state_changed

    async def set_ventilation_mode(self, mode: int) -> dict[str, Any]:
        """Set ventilation mode (0=Off, 1=Auto, 2=Level1, 3=Level2, 4=Level3)."""
        from .const import VarID
        return await self.write_variable(VarID.VENTILATION_MODE, mode)

    async def test_connection(self) -> bool:
        """Test the connection to the API."""
        try:
            # Try to read a single variable
            await self.read_variables(["1586i"])
            return True
        except (DimplexAuthError, DimplexApiError) as err:
            _LOGGER.error("Connection test failed: %s", err)
            return False


async def validate_credentials(
    refresh_token: str,
    session: aiohttp.ClientSession | None = None,
) -> tuple[str, str]:
    """Validate refresh token and return access token and new refresh token."""
    own_session = session is None
    if session is None:
        session = aiohttp.ClientSession()

    try:
        payload = {
            "grant_type": "refresh_token",
            "client_id": OAUTH2_CLIENT_ID,
            "client_secret": "",
            "redirect_uri": OAUTH2_REDIRECT_URI,
            "refresh_token": refresh_token,
        }

        async with session.post(
            OAUTH2_TOKEN_URL,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise DimplexAuthError(f"Invalid refresh token: {error_text}")

            data = await response.json()
            return data["access_token"], data.get("refresh_token", refresh_token)

    finally:
        if own_session:
            await session.close()


async def login_with_credentials(
    username: str,
    password: str,
    session: aiohttp.ClientSession | None = None,
) -> tuple[str, str]:
    """
    Login with username and password using Azure AD B2C flow.

    Returns tuple of (access_token, refresh_token).

    The flow is:
    1. GET /authorize -> get login page, CSRF token, cookies
    2. POST /SelfAsserted -> submit credentials (with manual Cookie header)
    3. GET /confirmed -> get authorization code via redirect
    4. POST /token -> exchange code for tokens
    """
    # We'll manage our own sessions since aiohttp has issues with pipe chars in cookie names
    initial_session = aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar(unsafe=True))

    try:
        _LOGGER.debug("Starting login flow for user: %s", username)

        # Step 1: Get the login page to obtain CSRF token and cookies
        authorize_params = {
            "client_id": OAUTH2_CLIENT_ID,
            "prompt": "login",
            "redirect_uri": OAUTH2_REDIRECT_URI,
            "response_type": "code",
            "scope": OAUTH2_SCOPE,
            "state": "glen_dimplex_1937",
            "ui_locales": "en",
        }

        authorize_url = f"{OAUTH2_AUTHORIZE_URL}?{urlencode(authorize_params)}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.98 Mobile Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        async with initial_session.get(authorize_url, headers=headers, allow_redirects=True) as response:
            if response.status != 200:
                raise DimplexLoginError(f"Failed to get login page: {response.status}")

            html = await response.text()

            # Extract CSRF token from the page
            csrf_match = re.search(r'"csrf":"([^"]+)"', html)
            if not csrf_match:
                raise DimplexLoginError("Could not find CSRF token in login page")
            csrf_token = csrf_match.group(1)

            # Extract transaction ID (StateProperties)
            trans_match = re.search(r'"transId":"([^"]+)"', html)
            if not trans_match:
                raise DimplexLoginError("Could not find transaction ID in login page")
            trans_id = trans_match.group(1)

            _LOGGER.debug("Got CSRF token and transaction ID")

            # Build cookie header manually (aiohttp has issues with pipe chars in cookie names)
            cookie_header = "; ".join([f"{c.key}={c.value}" for c in initial_session.cookie_jar])
            _LOGGER.debug("Cookies after authorize: %s", [c.key for c in initial_session.cookie_jar])

        # Step 2: Submit credentials via SelfAsserted endpoint
        self_asserted_url = f"https://gdtsb2c.b2clogin.com/gdtsb2c.onmicrosoft.com/B2C_1_signinsignupext/SelfAsserted?tx={trans_id}&p=B2C_1_signinsignupext"

        login_body = f"request_type=RESPONSE&logonIdentifier={quote_plus(username)}&password={quote_plus(password)}"

        login_headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.98 Mobile Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.9",
            "X-Requested-With": "XMLHttpRequest",
            "X-Csrf-Token": csrf_token,
            "Origin": "https://gdtsb2c.b2clogin.com",
            "Referer": authorize_url,
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Cookie": cookie_header,
        }

        _LOGGER.debug("SelfAsserted URL: %s", self_asserted_url)

        # Use fresh session with manual Cookie header
        async with aiohttp.ClientSession() as post_session:
            async with post_session.post(
                self_asserted_url,
                data=login_body,
                headers=login_headers,
            ) as response:
                response_text = await response.text()

                _LOGGER.debug("SelfAsserted response status: %s", response.status)

                if response.status != 200:
                    _LOGGER.error("Login failed: %s - %s", response.status, response_text)
                    raise DimplexLoginError(f"Login failed: {response.status}")

                # Check for error in response
                if '"status":"400"' in response_text or "AADB2C" in response_text:
                    error_match = re.search(r'"message":"([^"]+)"', response_text)
                    error_msg = error_match.group(1) if error_match else "Invalid credentials"
                    raise DimplexLoginError(f"Login failed: {error_msg}")

                _LOGGER.debug("Credentials accepted")

                # Extract updated cookie from Set-Cookie header
                set_cookie = response.headers.get('Set-Cookie', '')

        # Update cookies with the new one from Step 2
        if 'x-ms-cpim-cache' in set_cookie:
            new_cookie_part = set_cookie.split(';')[0]
            new_cookie_name = new_cookie_part.split('=')[0]

            # Replace old cookie with same name
            cookie_parts = cookie_header.split('; ')
            updated_parts = []
            for part in cookie_parts:
                if not part.startswith(new_cookie_name):
                    updated_parts.append(part)
            updated_parts.append(new_cookie_part)
            cookie_header = "; ".join(updated_parts)

        # Step 3: Get the authorization code via confirmed endpoint
        confirmed_url = f"https://gdtsb2c.b2clogin.com/gdtsb2c.onmicrosoft.com/B2C_1_signinsignupext/api/CombinedSigninAndSignup/confirmed?rememberMe=false&csrf_token={csrf_token}&tx={trans_id}&p=B2C_1_signinsignupext"

        confirmed_headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.98 Mobile Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": authorize_url,
            "Cookie": cookie_header,
        }

        async with aiohttp.ClientSession() as confirmed_session:
            async with confirmed_session.get(
                confirmed_url,
                headers=confirmed_headers,
                allow_redirects=False,
            ) as response:
                _LOGGER.debug("Confirmed response status: %s", response.status)

                redirect_url = response.headers.get("Location", "")

                if not redirect_url:
                    html = await response.text()
                    redirect_match = re.search(r'href="([^"]*code=[^"]+)"', html)
                    if redirect_match:
                        redirect_url = redirect_match.group(1)

                if not redirect_url or "code=" not in redirect_url:
                    _LOGGER.error("No authorization code in response")
                    raise DimplexLoginError("Could not obtain authorization code")

                # Parse the authorization code from the redirect URL
                parsed = urlparse(redirect_url)
                query_params = parse_qs(parsed.query)

                if "code" not in query_params:
                    raise DimplexLoginError("Authorization code not found in redirect")

                auth_code = query_params["code"][0]
                _LOGGER.debug("Got authorization code")

        # Step 4: Exchange authorization code for tokens
        token_data = {
            "grant_type": "authorization_code",
            "client_id": OAUTH2_CLIENT_ID,
            "code": auth_code,
            "redirect_uri": OAUTH2_REDIRECT_URI,
            "scope": OAUTH2_SCOPE,
        }

        async with aiohttp.ClientSession() as token_session:
            async with token_session.post(
                OAUTH2_TOKEN_URL,
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    _LOGGER.error("Token exchange failed: %s", error_text)
                    raise DimplexLoginError(f"Token exchange failed: {response.status}")

                data = await response.json()
                access_token = data["access_token"]
                refresh_token = data["refresh_token"]

                _LOGGER.info("Login successful for user: %s", username)
                return access_token, refresh_token

    except aiohttp.ClientError as err:
        _LOGGER.error("Network error during login: %s", err)
        raise DimplexLoginError(f"Network error: {err}") from err

    finally:
        await initial_session.close()
