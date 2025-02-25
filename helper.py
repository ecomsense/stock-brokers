class Helper:
    @staticmethod
    def get_side(side):
        if side[0].upper() == "B":
            return "BUY"
        else:
            return "SELL"

    @staticmethod
    def get_order_type(order_type):
        if order_type[0].upper() == "M":
            return "MARKET"
        elif order_type[0].upper() == "L":
            return "LIMIT"
        elif order_type.upper() == "SL":
            return "SL"
        else:
            return "SL-M"
