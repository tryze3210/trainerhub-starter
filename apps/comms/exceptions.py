class CommsError(Exception):
    pass


class TemplateRenderError(CommsError):
    pass


class PreferenceSuppressedError(CommsError):
    pass


class ProviderDispatchError(CommsError):
    pass
