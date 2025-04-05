class PaginationError(Exception):
    pass


class PageOutOfRangeError(PaginationError):
    pass
