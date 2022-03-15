from ..overload import overload

class Vector:
    def __init__(self, y: int, x: int):
        self.y = y
        self.x = x

    @overload # type: ignore
    def add(self, y: int, x: int) -> 'Vector':
        self.y += y
        self.x += x
        return self

    @overload # type: ignore
    def add(self, vec: 'Vector') -> 'Vector':
        return self.add(vec.y, vec.x)

    @overload # type: ignore
    def sub(self, y: int, x: int) -> 'Vector':
        self.y -= y
        self.x -= x
        return self

    @overload # type: ignore
    def sub(self, vec: 'Vector') -> 'Vector':
        return self.sub(vec.y, vec.x)

    def mul(self, val: int) -> 'Vector':
        self.y *= val
        self.x *= val
        return self

    def floordiv(self, val: int) -> 'Vector':
        self.y //= val
        self.x //= val
        return self

    def neg(self) -> 'Vector':
        self.y = -self.y
        self.x = -self.x
        return self

    def abs(self) -> 'Vector':
        self.y = abs(self.y)
        self.x = abs(self.x)
        return self

    def copy(self) -> 'Vector':
        return Vector(self.y, self.x)

    def __add__(self, vec: 'Vector') -> 'Vector':
        return self.copy().add(vec)

    def __sub__(self, vec: 'Vector') -> 'Vector':
        return self.copy().sub(vec)

    def __mul__(self, val: int) -> 'Vector':
        return self.copy().mul(val)

    def __floordiv__(self, val: int) -> 'Vector':
        return self.copy().floordiv(val)

    def __iadd__(self, vec: 'Vector') -> 'Vector':
        return self.add(vec)

    def __isub__(self, vec: 'Vector') -> 'Vector':
        return self.sub(vec)

    def __imul__(self, val: int) -> 'Vector':
        return self.mul(val)

    def __ifloordiv__(self, val: int) -> 'Vector':
        return self.floordiv(val)

    def __neg__(self) -> 'Vector':
        return self.copy().neg()

    def __abs__(self) -> 'Vector':
        return self.copy().abs()

    def __eq__(self, v) -> bool:
        if not isinstance(v, Vector):
            return NotImplemented
        return self.y == v.y and self.x == v.x

    def __ne__(self, v) -> bool:
        if not isinstance(v, Vector):
            return NotImplemented
        return self.y != v.y or self.x != v.x

    def __str__(self) -> str:
        return f'<{self.y}, {self.x}>'

    def __bool__(self) -> bool:
        return self.y != 0 or self.x != 0
