class WereadVaultError(Exception):
    """Expected command failure with an actionable message."""


class GatewayError(WereadVaultError):
    """The WeRead gateway could not complete a request."""


class SkillUpgradeRequired(WereadVaultError):
    """The upstream Skill version is no longer accepted."""
