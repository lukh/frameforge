
import os
from collections import defaultdict

import FreeCAD as App
import FreeCADGui as Gui


from freecad.frameforge.ff_tools import ICONPATH, PROFILEIMAGES_PATH, PROFILESPATH, UIPATH, translate


def letters_to_int(s: str) -> int:
    """
    'A' -> 1
    'Z' -> 26
    'AA' -> 27
    """
    s = s.strip().upper()
    value = 0
    for c in s:
        if not ('A' <= c <= 'Z'):
            raise ValueError(f"Invalid letter ID: {s}")
        value = value * 26 + (ord(c) - ord('A') + 1)
    return value


def int_to_letters(n: int) -> str:
    """
    1 -> 'A'
    26 -> 'Z'
    27 -> 'AA'
    """
    if n <= 0:
        raise ValueError("Letter IDs must be >= 1")

    result = []
    while n > 0:
        n -= 1
        n, r = divmod(n, 26)
        result.append(chr(ord('A') + r))
    return ''.join(reversed(result))


def number_str_to_int(s: str) -> int:
    return int(s)

def int_to_number_str(n: int) -> str:
    if n <= 0:
        raise ValueError("Numeric IDs must be >= 1")
    return str(n)




class IdGenerator:
    def __init__(self, used_ids: set[str], mode: str,
                 strategy: str,
                 start_value: str | None = None):
        """
        mode: "number" or "letter"
        strategy: "start_at", "continue", "fill_gaps"
        start_value: string, e.g. "1" or "A"
        """
        self.mode = mode
        self.strategy = strategy

        # Choose converters
        if mode == "number":
            self.to_int = number_str_to_int
            self.from_int = int_to_number_str
        elif mode == "letter":
            self.to_int = letters_to_int
            self.from_int = int_to_letters
        else:
            raise ValueError("mode must be 'number' or 'letter'")

        # Convert used ids to ints
        self.used = set()
        for s in used_ids:
            try:
                self.used.add(self.to_int(s))
            except Exception:
                pass  # ignore invalid IDs if needed

        # Initialize cursor
        if strategy == "start_at":
            if start_value is None:
                raise ValueError("start_value required for start_at")
            self.cursor = self.to_int(start_value)

        elif strategy == "continue":
            self.cursor = max(self.used) + 1 if self.used else 1

        elif strategy == "fill_gaps":
            self.cursor = 1

        else:
            raise ValueError("Unknown strategy")

    def next(self) -> str:
        n = self.cursor

        if self.strategy == "fill_gaps":
            while n in self.used:
                n += 1
        else:
            while n in self.used:
                n += 1

        # Reserve it
        self.used.add(n)

        # Move cursor forward for next call
        self.cursor = n + 1

        return self.from_int(n)




def populate_ids(sel_profiles, sel_links, doc_profiles, doc_links, 
            numbering_type, 
            allow_duplicated, 
            reset_existing, 
            numbering_scheme, 
            start_number="1", start_letter="A"
        ):

    if reset_existing:
        for sp in sel_profiles:
            sp.PID = ""
        for sl in sel_links:
            sl.PID = ""

    if allow_duplicated:
        profiles_used = {}
        links_used = {}

    else:
        if numbering_scheme == "fill_selection":
            profiles_used = {o.PID for o in sel_profiles if o.PID}
            links_used = {o.PID for o in sel_links if o.PID}
        else:
            profiles_used = {getattr(o, "PID", "") for o in doc_profiles if getattr(o, "PID", "")} - {getattr(o, "PID", "") for o in sel_profiles if getattr(o, "PID", "")}
            links_used = {getattr(o, "PID", "") for o in doc_links if getattr(o, "PID", "")} - {getattr(o, "PID", "") for o in sel_links if getattr(o, "PID", "")}


    if numbering_scheme in ["fill_selection", "fill_document"]:
        strategy = "fill_gaps"
    elif numbering_scheme == "continue_document":
        strategy = "continue"
    elif numbering_scheme == "start_at":
        strategy = "start_at"
    else:
        raise ValueError('Wrong numbering_scheme')



    if numbering_type == "all_numbers":
        gen_profiles = IdGenerator(profiles_used | links_used, mode="number", strategy=strategy, start_value=start_number)
        gen_links = gen_profiles

    elif numbering_type == "all_letters":
        gen_profiles = IdGenerator(profiles_used | links_used, mode="letter", strategy=strategy, start_value=start_letter)
        gen_links = gen_profiles

    elif numbering_type == "number_for_profiles_letters_for_links":
        gen_profiles = IdGenerator(profiles_used, mode="number", strategy=strategy, start_value=start_number)
        gen_links = IdGenerator(links_used, mode="letter", strategy=strategy, start_value=start_letter)

    elif numbering_type == "letters_for_profiles_number_for_links":
        gen_profiles = IdGenerator(profiles_used, mode="letter", strategy=strategy, start_value=start_letter)
        gen_links = IdGenerator(links_used, mode="number", strategy=strategy, start_value=start_number)
    else:
        raise ValueError('Wrong numbering_type')

    for sp in sel_profiles:
        sp.PID = gen_profiles.next()
    for sl in sel_links:
        sl.PID = gen_links.next()
