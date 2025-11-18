class OrderPlacementError(Exception):
    """
    Raised when order placement at stock exchange fails.
    """

    pass


class OrderSaveError(Exception):
    """
    Raised when saving an order to the DB fails.
    """

    pass
