from eodhp_utils.messagers import TemporaryFailure


class MissingParentError(TemporaryFailure):
    pass


class SFAPIConnectionError(TemporaryFailure):
    pass


class InvalidSTACException(Exception):
    pass
