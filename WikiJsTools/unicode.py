####################################################################################################
#
# wikijs-cli - A CLI for Wiki.js
# Copyright (C) 2025 Fabrice SALVAIRE
# SPDX-License-Identifier: GPL-3.0-or-later
#
####################################################################################################

__all__ = ['usorted']

####################################################################################################

# To sort correctly latin and unicode
from icu import Collator, Locale

# Fixme:
collator = Collator.createInstance(Locale('fr_FR'))

####################################################################################################

def usorted(iter: list, key: str = None) -> list:
    if key is not None:
        return sorted(iter, key=lambda _: collator.getSortKey(getattr(_, key)))
    else:
        return sorted(iter, key=lambda _: collator.getSortKey)
