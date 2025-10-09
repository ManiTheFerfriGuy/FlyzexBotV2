import asyncio
from urllib.parse import urlparse, parse_qs

from webapp.avatar import AvatarService


def test_avatar_service_placeholder_generates_consistent_url() -> None:
    service = AvatarService(bot_token=None)

    async def runner() -> None:
        try:
            first = await service.get_avatar_url(user_id=42)
            assert first is not None
            parsed = urlparse(first)
            assert parsed.scheme in {"http", "https"}
            assert parsed.netloc
            params = parse_qs(parsed.query)
            assert params.get("seed") == ["42"]

            second = await service.get_avatar_url(username="ExampleUser")
            assert second is not None
            assert "ExampleUser".lower() in parse_qs(urlparse(second).query)["seed"][0]

            cached = await service.get_avatar_url(user_id=42)
            assert cached == first
        finally:
            await service.close()

    asyncio.run(runner())


def test_avatar_service_prefers_username_cache() -> None:
    service = AvatarService(bot_token=None)

    async def runner() -> None:
        try:
            first = await service.get_avatar_url(username="SampleUser")
            second = await service.get_avatar_url(username="SampleUser")
            assert first == second
        finally:
            await service.close()

    asyncio.run(runner())
