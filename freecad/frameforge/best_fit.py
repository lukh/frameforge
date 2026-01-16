class CutPart:
    def __init__(self, name, length, kerf, obj=None):
        self.name = name
        self.length = length
        self.kerf = kerf
        self.obj = obj

    @property
    def cut_size(self):
        return self.length + self.kerf

    def __str__(self):
        return f"CutPart<{self.name}>={self.length}"

    def __repr__(self):
        return self.__str__()


class Stock:
    def __init__(self, length):
        self.length = length
        self._parts = []

    def __str__(self):
        return f"Stock<{self.length}, used={self.used}, left={self.left}> = {self._parts}"

    def __repr__(self):
        return self.__str__()

    @property
    def used(self):
        return sum([p.cut_size for p in self._parts])

    @property
    def left(self):
        return self.length - self.used

    def add_part(self, part):
        if part.cut_size <= self.left:
            self._parts.append(part)
        else:
            raise ValueError(f"Can't fit {part.name} ({part.length}) in {self.length}")

    @property
    def parts(self):
        return self._parts


def best_fit_decreasing(l_stock, parts):
    sorted_parts = sorted(parts, key=lambda x: x.cut_size, reverse=True)

    stocks = []
    for p in sorted_parts:
        # on choisit celle qui laisse le moins d’espace libre après placement
        sorted_stocks = list(filter(lambda x: (x.left - p.cut_size) >= 0.0, sorted(stocks, key=lambda s: s.left)))
        if len(sorted_stocks) == 0:
            stock = Stock(l_stock)
            stocks.append(stock)
        else:
            stock = sorted_stocks[0]
        stock.add_part(p)

    return stocks
