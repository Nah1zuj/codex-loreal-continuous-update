"""Namespaced HTTP extensions; each extension owns its authorization rules."""
from collections.abc import Callable, Iterable
from dataclasses import dataclass
import re
from typing import TYPE_CHECKING
from fastapi import APIRouter
if TYPE_CHECKING:
    from app.composition import ApplicationServices


@dataclass(frozen=True)
class ExtensionSpec:
    name: str
    build_router: Callable[['ApplicationServices'], APIRouter]


def validate_extensions(extensions: Iterable[ExtensionSpec]) -> tuple[ExtensionSpec, ...]:
    result = tuple(extensions)
    names = set()
    for extension in result:
        if not isinstance(extension, ExtensionSpec):
            raise TypeError('Expected ExtensionSpec')
        if not isinstance(extension.name, str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,39}', extension.name):
            raise ValueError('Extension name must be a lowercase namespace')
        if extension.name in names:
            raise ValueError(f'Duplicate extension namespace: {extension.name}')
        if not callable(extension.build_router):
            raise TypeError('Extension router factory must be callable')
        names.add(extension.name)
    return result
