from __future__ import annotations

import unittest
import urllib.error
from unittest import mock

from weread_vault.gateway import Gateway, _can_retry_with_curl


class GatewayFallbackTests(unittest.TestCase):
    def test_certificate_verify_failure_uses_curl_fallback(self):
        gateway = Gateway(api_key="test-key")

        with mock.patch("weread_vault.gateway.urllib.request.urlopen") as urlopen:
            urlopen.side_effect = urllib.error.URLError(
                "[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed"
            )
            with mock.patch.object(gateway, "_post_with_curl", return_value={"errcode": 0, "ok": True}) as fallback:
                self.assertEqual(gateway._post({"api_name": "/shelf/sync"}), {"errcode": 0, "ok": True})
                fallback.assert_called_once_with({"api_name": "/shelf/sync"})

    def test_only_expected_tls_errors_fallback_to_curl(self):
        self.assertTrue(_can_retry_with_curl(urllib.error.URLError("unknown url type: https")))
        self.assertTrue(_can_retry_with_curl(urllib.error.URLError("[SSL: CERTIFICATE_VERIFY_FAILED] bad ca")))
        self.assertFalse(_can_retry_with_curl(urllib.error.URLError("timed out")))


if __name__ == "__main__":
    unittest.main()
