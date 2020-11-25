_global_config = {'db_name': 'datakyt',
                  'db_admin': 'datakyt_admin',
                  'db_password': ''}


def get_config() -> dict:
    return _global_config.copy()


def set_config(params: dict):
    if type(params) is not dict:
        raise TypeError(f"Dict expected, got {type(params)} instead")
    for param, value in params.items():
        if value is not None:
            _global_config[param] = value
