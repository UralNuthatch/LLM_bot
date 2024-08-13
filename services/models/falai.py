import asyncio
import aiofiles
import aiohttp
import fal_client


async def response_falai_model_img(model, prompt: str, telegram_id: int):
    handler = await fal_client.submit_async(
        f"fal-ai/{model}",
        arguments={
            "prompt": prompt
        },
    )

    log_index = 0
    async for event in handler.iter_events(with_logs=True):
        if isinstance(event, fal_client.InProgress):
            new_logs = event.logs[log_index:]
            # for log in new_logs:
            #     print(log["message"])
            log_index = len(event.logs)

    result = await handler.get()
    url = result['images'][0]['url']

    # Асинхронное скачивание файла
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            async with aiofiles.open(f"{telegram_id}_0.png", "wb") as f:
                while True:
                    chunk = await response.content.read(1024)
                    if not chunk:
                        break
                    await f.write(chunk)