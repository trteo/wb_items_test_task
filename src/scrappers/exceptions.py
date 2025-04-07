class ContentError(Exception):
    pass


class ProductNotFound(ContentError):
    pass


class CatalogFindItemsError(ContentError):
    pass
