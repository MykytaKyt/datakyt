_global_config = {'db_name': 'datakyt',
                  'db_admin': 'datakyt_admin',
                  'db_password': ''}


def get_config() -> dict:
    """Retrieve current values for configuration set by :func:`set_config`
    Returns
    -------
    config : dict
        Keys are config names that can be passed to :func:`set_config`.
    """
    return _global_config.copy()


def set_config(params: dict):
    """Set global datakyt configuration
    Parameters
    ----------
    params : dict
        If None passed as a new config value, _global_config won't be changed.
        If an existing config name was passed as a dict key with a not-None value, the corresponded
        config in _global_config will be changed to passed value.
        If non-existing config name was passed as a dict key with a not-None value, the new config
        will be created in _global_config.
    """
    if type(params) is not dict:
        raise TypeError(f"Dict expected, got {type(params)} instead")
    for param, value in params.items():
        if value is not None:
            _global_config[param] = value
