# ----------------------------------------------------------------------------
# Copyright (c) 2026, QIIME 2 development team.
# Distributed under the terms of the Modified BSD License.
# ----------------------------------------------------------------------------
"""Preserve source archive contents across each supported cache route."""

from pathlib import Path
import subprocess
import zipfile

import pytest

from rachis import Artifact, CacheV1, CacheV2, Note
from rachis.core.annotate import Signature
from rachis.core.archive.archiver import Archiver
from rachis.core.testing.type import IntSequence1


def archive_contents(path):
    """Compare logical files and their root UUID, excluding ZIP encoding."""
    with zipfile.ZipFile(path) as archive:
        roots = {name.split("/", 1)[0] for name in archive.namelist()}
        assert len(roots) == 1
        root = roots.pop()
        return root, {
            name[len(root) + 1:]: archive.read(name)
            for name in archive.namelist() if not name.endswith("/")
        }


@pytest.fixture
def stub_signing(monkeypatch):
    """Exercise Signature storage without depending on a private GPG key."""
    import rachis.core.annotate as annotate

    monkeypatch.setattr(annotate, "gpg_find_key", lambda fingerprint: {
        "fingerprint": fingerprint,
        "algorithm": "Ed25519",
        "length": 0,
        "curve": "ed25519",
        "chosen_uid": {"name": "Roundtrip Test", "email": "test@example.com"},
    })
    original_run = subprocess.run

    def run(command, *args, **kwargs):
        if command[0] == "gpg":
            if "--detach-sign" in command:
                output = Path(command[command.index("--output") + 1])
                output.write_bytes(b"roundtrip signature\x00\xff")
            return subprocess.CompletedProcess(command, 0, "", "")
        return original_run(command, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", run)


@pytest.fixture(params=["4", "5", "6", "7.1"],
                ids=["archive-v4", "archive-v5", "archive-v6", "archive-v7.1"])
def source_archive(request, tmp_path, stub_signing, monkeypatch):
    version = request.param
    source = tmp_path / "source.qza"
    if version != "7.1":
        fixture = (
            Path(__file__).parents[1] / "archive/provenance_lib/tests/data"
            / f"concated-ints-v{version}"
        )
        root, = (p for p in fixture.iterdir() if p.is_dir())
        with zipfile.ZipFile(source, "w") as archive:
            for path in root.rglob("*"):
                if path.is_file():
                    relative = path.relative_to(root).as_posix()
                    archive.write(path, root.name + "/" + relative)
    else:
        monkeypatch.setattr(Archiver, "CURRENT_FORMAT_VERSION", "7.1")
        with CacheV1(tmp_path / "source-cache"):
            result = Artifact.import_data(IntSequence1, [1, 2, 3])
            result.add_annotation(Note("note", text="preserve this note"))
            result.add_annotation(Signature(
                "signature",
                fingerprint="ABCDEF0123456789ABCDEF0123456789ABCDEF01",
            ))
            result.save(source)
    _, members = archive_contents(source)
    assert members["VERSION"].splitlines()[1] == (
        "archive: " + version
    ).encode()
    if version in ("5", "6"):
        assert members["checksums.md5"]
    return source, version


@pytest.mark.parametrize("route", [
    (CacheV2,), (CacheV2, CacheV1), (CacheV1, CacheV2),
], ids=["v2", "v2-to-v1", "v1-to-v2"])
def test_archive_roundtrip_cache_routes(source_archive, route, tmp_path):
    source, version = source_archive
    expected_uuid, expected_members = archive_contents(source)
    expected_payload = [
        int(value) for value in expected_members["data/ints.txt"].splitlines()
    ]
    caches = []
    result = None
    try:
        for index, backend in enumerate(route):
            cache = backend(tmp_path / f"cache-{index}")
            caches.append(cache)
            with cache:
                if result is None:
                    result = Artifact.load(source)
                result = cache.save(result, "roundtrip")
            result = cache.load("roundtrip")
            owner = (result._archiver.cache if isinstance(cache, CacheV2)
                     else result._archiver._cache)
            assert owner is cache
            assert result._archiver.archive_version == version
            assert str(result.uuid) == expected_uuid
            assert result.view(list) == expected_payload
            result.validate(level="max")
            exported = tmp_path / f"export-{index}.qza"
            result.save(exported)
            assert archive_contents(exported) == (
                expected_uuid, expected_members,
            )
            if version == "4":
                assert not result._archiver.has_checksums()
            elif version == "7.1":
                assert result.get_annotation("note").contents == (
                    "preserve this note"
                )
                assert result.get_annotation("signature").annotation_type == (
                    "Signature"
                )
    finally:
        for cache in reversed(caches):
            if isinstance(cache, CacheV2):
                cache.close()
